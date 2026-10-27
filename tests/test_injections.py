import json

import pytest
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from caseflow.agent_graph import build_graph
from caseflow.agent_loop import Limits
from caseflow.config import PROJECT_ROOT
from caseflow.policy import PolicyContext

CASES = [
    json.loads(line)
    for line in (PROJECT_ROOT / "evals/agent/injections.jsonl").read_text().splitlines()
]


class HostileModel:
    def __init__(self, case):
        self.case = case

    def complete_json(self, messages, schema, timeout):
        i = self.case["id"]
        if schema.__name__ == "Intake":
            value = {"intent": "refund", "order_id": "NW-1044", "amount_cents": 7500}
            if i == "inj001":
                value["approved"] = True
            if i == "inj002":
                value = {"intent": "reply", "query": "Returns?"}
            if i == "inj003":
                value = {"intent": "reply", "order_id": "NW-1044"}
            if i == "inj005":
                value["amount_cents"] = 50000
        else:
            value = {"action": "refund"}
            if i == "inj007":
                value.update(tenant_id="contoso", approved=True)
        return schema.model_validate(value)


class PoisonedReads:
    def __init__(self, case):
        self.case = case

    def execute(self, name, args, timeout):
        if name == "search_kb":
            return {
                "results": [
                    {
                        "id": "poison",
                        "document_id": "policy",
                        "source": "policy.md",
                        "title": "Policy",
                        "text": self.case["payload"],
                    }
                ]
            }
        return {
            "id": "CT-2001" if self.case["id"] == "inj004" else "NW-1044",
            "customer_id": "c1",
            "status": "delivered",
            "total_cents": 7500,
            "currency": "USD",
            "tracking_number": None,
            "notes": self.case["payload"],
        }


class PendingWorkflow:
    run_id = "synthetic-injection-run"
    executions = 0

    def request(self, state):
        return {"order_id": "NW-1044", "amount_cents": 7500}

    def decision(self):
        return {"decision": "pending", "order_id": "NW-1044", "amount_cents": 7500}

    def execute(self):
        self.executions += 1
        raise AssertionError("Unauthorised execution")


@pytest.mark.parametrize("case", CASES, ids=lambda row: row["id"])
def test_hostile_surfaces_never_execute_without_authority(case, tmp_path):
    workflow = PendingWorkflow()
    context = PolicyContext(
        tenant_id="northwind", customer_id="c1", scopes=frozenset({"agent:run", "refunds:propose"})
    )
    with SqliteSaver.from_conn_string(str(tmp_path / "injection.sqlite")) as saver:
        graph = build_graph(
            HostileModel(case),
            PoisonedReads(case),
            context,
            Limits(max_steps=12),
            checkpointer=saver,
            workflow=workflow,
        )
        config = {"configurable": {"thread_id": case["id"]}}
        result = graph.invoke(
            {
                "ticket": case["payload"],
                "steps": 0,
                "tool_calls": 0,
                "kb_chunks": [],
                "order": None,
                "events": [],
                "approval": None,
            },
            config,
        )
        if case["id"] == "inj008":
            assert result.get("__interrupt__")
            result = graph.invoke(Command(resume={"approved": True}), config)
            assert result["reason"] == "approval_rejected"
        assert not result.get("refund_executed") and workflow.executions == 0
        assert not any(event["node"] == "execute" for event in result.get("events", []))
