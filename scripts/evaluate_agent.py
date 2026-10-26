"""Model quality on immutable fictional orders + real KB reads; no refund writes."""

import argparse
import json
import os
import time
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from support_copilot.agent_evaluation import dataset_hash, judge, load_scenarios
from support_copilot.agent_graph import GraphModel, run_graph
from support_copilot.agent_tools import BoundTools, OrderArgs, RecordNotFound
from support_copilot.auth import Principal
from support_copilot.config import PROJECT_ROOT, Settings
from support_copilot.mock_backend import Fixtures


class EvaluationReads:
    def __init__(self, tenant, knowledge_url, fixtures):
        self.principal = Principal(
            tenant,
            frozenset({"agent:run", "kb:read", "orders:read", "refunds:propose"}),
            "synthetic-evaluation",
        )
        self.fixtures = fixtures
        self.knowledge = BoundTools(
            self.principal,
            knowledge_url,
            "http://127.0.0.1:1",
            os.getenv(tenant.upper() + "_API_TOKEN", ""),
            "unused-fixture-token",
        )

    def execute(self, name, args, timeout):
        if name == "search_kb":
            return self.knowledge.execute(name, args, timeout)
        if name != "get_order":
            raise ValueError("Unknown read")
        order_id = OrderArgs.model_validate(args).order_id
        row = next(
            (
                o
                for o in self.fixtures.orders
                if o.tenant_id == self.principal.tenant_id and o.id == order_id
            ),
            None,
        )
        if row is None:
            raise RecordNotFound("Record not found")
        return row.model_dump(mode="json")


def main():
    cfg = Settings.from_env()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["hosted", "local"], required=True)
    parser.add_argument("--knowledge-url", default="https://16-178-30-70.sslip.io")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pause-seconds", type=float, default=3)
    args = parser.parse_args()
    if not 0 <= args.pause_seconds <= 60:
        parser.error("Pause must be 0 through 60 seconds")
    if args.provider == "hosted":
        cfg = replace(
            cfg,
            llm_provider="openai_compatible",
            llm_model="openai/gpt-oss-20b",
            llm_base_url="https://api.groq.com/openai/v1",
            llm_timeout=60,
        )
    else:
        cfg = replace(
            cfg,
            llm_provider="ollama",
            llm_model="qwen3:4b",
            llm_base_url="http://localhost:11434",
            llm_api_key="",
            llm_timeout=60,
        )
    path = PROJECT_ROOT / "evals/agent/scenarios.jsonl"
    fixtures = Fixtures.model_validate_json((PROJECT_ROOT / "data/mock/entities.json").read_text())
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "provider": args.provider,
        "model": cfg.llm_model,
        "dataset_sha256": dataset_hash(path),
        "order_fixture_sha256": dataset_hash(PROJECT_ROOT / "data/mock/entities.json"),
        "dataset_kind": "synthetic development; immutable order reads and real KB retrieval",
        "approval_stage": "non-durable placeholder; durable authority tested separately",
        "settings": {
            "strict_schema": True,
            "hosted_max_tokens": 1200,
            "hosted_reasoning_effort": "low",
            "call_timeout_seconds": 60,
            "run_timeout_seconds": 120,
            "node_limit": 6,
            "pause_between_cases_seconds": args.pause_seconds,
        },
        "results": [],
    }
    model = GraphModel(cfg)
    for scenario in load_scenarios(path):
        result = run_graph(
            scenario.ticket,
            model,
            EvaluationReads(scenario.tenant, args.knowledge_url, fixtures),
            customer_id=scenario.customer_id,
        )
        passed = judge(scenario, result, PROJECT_ROOT / "data", approval_placeholder=True)
        report["results"].append({"id": scenario.id, "passed": passed, "result": result})
        report.update(
            scenarios=len(report["results"]),
            passed=sum(r["passed"] for r in report["results"]),
            complete=len(report["results"]) == 25,
        )
        report["success_rate"] = report["passed"] / report["scenarios"]
        report["rate_limit_retries"] = model.retry_count
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
        print(
            json.dumps(
                {
                    "id": scenario.id,
                    "passed": passed,
                    "reason": result["reason"],
                    "diagnostic": result.get("diagnostic", {}),
                }
            ),
            flush=True,
        )
        time.sleep(args.pause_seconds)
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(
            f"Evaluation failed ({type(exc).__name__}); raw details withheld"
        ) from None
