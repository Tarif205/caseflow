"""Trusted local Day 6 runner; no agent HTTP deployment or refund execution."""

import argparse
import json
import os
import time
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from support_copilot.agent_evaluation import dataset_hash, judge, load_scenarios
from support_copilot.agent_graph import GraphModel, run_graph
from support_copilot.agent_loop import Limits, run_agent
from support_copilot.agent_tools import BoundTools
from support_copilot.auth import authenticate
from support_copilot.config import PROJECT_ROOT, Settings
from support_copilot.database import connect
from support_copilot.tool_chat import HttpToolModel


def main():
    cfg = Settings.from_env()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["hosted", "local"], required=True)
    parser.add_argument("--engine", choices=["loop", "graph"], default="loop")
    parser.add_argument(
        "--knowledge-url", default=os.getenv("KNOWLEDGE_API_URL", "http://127.0.0.1:8001")
    )
    parser.add_argument(
        "--backend-url", default=os.getenv("MOCK_BACKEND_URL", "http://127.0.0.1:8004")
    )
    parser.add_argument("--tenant", choices=["northwind", "contoso"], default="northwind")
    parser.add_argument("--ticket")
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument(
        "--scenarios", type=Path, default=PROJECT_ROOT / "evals/agent/scenarios.jsonl"
    )
    parser.add_argument("--max-steps", type=int, default=6)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if bool(args.ticket) == args.evaluate or not 1 <= args.count <= 25:
        parser.error("Choose one of --ticket or --evaluate; count must be 1 through 25")
    if args.provider == "hosted":
        model_cfg = replace(
            cfg,
            llm_provider="openai_compatible",
            llm_base_url="https://api.groq.com/openai/v1",
            llm_model="openai/gpt-oss-20b",
            llm_timeout=min(args.timeout, 60),
        )
    else:
        model_cfg = replace(
            cfg,
            llm_provider="ollama",
            llm_base_url="http://localhost:11434",
            llm_model="qwen3:4b",
            llm_api_key="",
            llm_timeout=min(args.timeout, 60),
        )
    limits = Limits(max_steps=args.max_steps, timeout_seconds=args.timeout)

    def bound(tenant):
        backend_token = os.getenv(tenant.upper() + "_AGENT_API_TOKEN", "")
        with connect(cfg) as conn:
            principal = authenticate(conn, backend_token)
        if principal is None or principal.tenant_id != tenant:
            raise ValueError("Provision the tenant's local agent token first")
        return BoundTools(
            principal,
            args.knowledge_url,
            args.backend_url,
            os.getenv(tenant.upper() + "_API_TOKEN", ""),
            backend_token,
        )

    try:
        model = GraphModel(model_cfg) if args.engine == "graph" else HttpToolModel(model_cfg)
        run = run_graph if args.engine == "graph" else run_agent
        if args.ticket:
            report = run(args.ticket, model, bound(args.tenant), limits)
        else:
            path = args.scenarios
            scenarios = load_scenarios(path)
            if args.count > len(scenarios):
                raise ValueError("Requested count exceeds available scenarios")
            rows = []
            for scenario in scenarios[: args.count]:
                result = run(scenario.ticket, model, bound(scenario.tenant), limits)
                rows.append(
                    {
                        "id": scenario.id,
                        "passed": judge(
                            scenario,
                            result,
                            PROJECT_ROOT / "data",
                            approval_placeholder=args.engine == "graph",
                        ),
                        "result": result,
                    }
                )
                print(
                    json.dumps(
                        {
                            "scenario": scenario.id,
                            "status": result["status"],
                            "reason": result["reason"],
                            "passed": rows[-1]["passed"],
                        }
                    ),
                    flush=True,
                )
                time.sleep(2)
            report = {
                "checked_at": datetime.now(UTC).isoformat(),
                "provider": args.provider,
                "engine": args.engine,
                "approval_stage": "non-durable placeholder"
                if args.engine == "graph"
                else "unavailable",
                "model": model_cfg.llm_model,
                "dataset_sha256": dataset_hash(path),
                "dataset_kind": "assistant-authored synthetic development fixtures; not held-out",
                "knowledge_url": args.knowledge_url,
                "backend_url": args.backend_url,
                "limits": {
                    "steps": limits.max_steps,
                    "step_unit": "graph node" if args.engine == "graph" else "model turn",
                    "tool_calls": limits.max_tool_calls,
                    "timeout_seconds": limits.timeout_seconds,
                },
                "scenarios": len(rows),
                "passed": sum(r["passed"] for r in rows),
                "success_rate": sum(r["passed"] for r in rows) / len(rows),
                "results": rows,
                "limitations": "Evidence selection/expected-order checks only, not semantic completeness or production safety.",
            }
    except Exception as exc:
        # Driver/provider exceptions can contain credentials. No traceback or raw body.
        raise SystemExit(
            f"Agent setup failed ({type(exc).__name__}); check safe local configuration"
        ) from None
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2, default=str))


if __name__ == "__main__":
    main()
