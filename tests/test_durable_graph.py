from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from support_copilot.agent_graph import build_graph
from support_copilot.agent_loop import Limits
from support_copilot.policy import PolicyContext


class Model:
    def complete_json(self, messages, schema, timeout):
        return schema.model_validate(
            {"intent": "refund", "order_id": "NW-1044"}
            if schema.__name__ == "Intake"
            else {"action": "refund"}
        )


class Tools:
    def execute(self, name, args, timeout):
        return {
            "id": "NW-1044",
            "customer_id": "c1",
            "status": "delivered",
            "total_cents": 7500,
            "currency": "USD",
            "tracking_number": None,
        }


class Workflow:
    run_id = "test-run"
    state = "pending"
    executions = 0

    def request(self, state):
        assert state["intake"]["amount_cents"] == 7500
        return {"order_id": "NW-1044", "amount_cents": 7500}

    def decision(self):
        return {**self.request({"intake": {"amount_cents": 7500}}), "decision": self.state}

    def execute(self):
        assert self.state == "approved"
        self.executions += 1
        return {"order_id": "NW-1044", "amount_cents": 7500}


def compile_graph(path, workflow):
    saver_context = SqliteSaver.from_conn_string(str(path))
    saver = saver_context.__enter__()
    graph = build_graph(
        Model(),
        Tools(),
        PolicyContext(
            tenant_id="test", customer_id="c1", scopes=frozenset({"agent:run", "refunds:propose"})
        ),
        Limits(max_steps=12),
        checkpointer=saver,
        workflow=workflow,
    )
    return saver_context, graph


def initial():
    return {
        "ticket": "Full refund please",
        "tenant_id": "test",
        "steps": 0,
        "tool_calls": 0,
        "kb_chunks": [],
        "order": None,
        "events": [],
        "approval": None,
    }


def test_forged_resume_value_does_not_substitute_for_stored_decision(tmp_path):
    workflow = Workflow()
    context, graph = compile_graph(tmp_path / "agent.sqlite", workflow)
    try:
        config = {"configurable": {"thread_id": "test:run"}}
        first = graph.invoke(initial(), config)
        assert first["__interrupt__"]
        result = graph.invoke(Command(resume={"approved": True}), config)
        assert result["reason"] == "approval_rejected" and workflow.executions == 0
    finally:
        context.__exit__(None, None, None)


def test_stored_rejection_survives_checkpoint_reopen(tmp_path):
    workflow = Workflow()
    path = tmp_path / "agent.sqlite"
    config = {"configurable": {"thread_id": "test:run"}}
    context, graph = compile_graph(path, workflow)
    graph.invoke(initial(), config)
    context.__exit__(None, None, None)
    workflow.state = "rejected"
    context, graph = compile_graph(path, workflow)
    try:
        result = graph.invoke(Command(resume="wake"), config)
        assert result["reason"] == "approval_rejected" and not workflow.executions
    finally:
        context.__exit__(None, None, None)


def test_committed_refund_receipt_is_preserved_if_deadline_passes_after_commit(tmp_path):
    now = [0.0]

    class SlowCommittedWorkflow(Workflow):
        state = "approved"

        def execute(self):
            result = super().execute()
            now[0] = 200
            return result

    workflow = SlowCommittedWorkflow()
    with SqliteSaver.from_conn_string(str(tmp_path / "deadline.sqlite")) as saver:
        graph = build_graph(
            Model(),
            Tools(),
            PolicyContext(
                tenant_id="test",
                customer_id="c1",
                scopes=frozenset({"agent:run", "refunds:propose"}),
            ),
            Limits(max_steps=12),
            clock=lambda: now[0],
            checkpointer=saver,
            workflow=workflow,
        )
        config = {"configurable": {"thread_id": "test:deadline"}}
        graph.invoke(initial(), config)
        result = graph.invoke(Command(resume="wake"), config)
        assert result["status"] == "refunded" and result["refund_executed"]
