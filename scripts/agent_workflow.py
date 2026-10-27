"""Local human workflow. Approve/reject are explicit operator commands, never model tools."""

import argparse
import json
import os
from dataclasses import replace
from pathlib import Path

from caseflow.agent_graph import GraphModel
from caseflow.approvals import ApprovalStore
from caseflow.auth import authenticate
from caseflow.config import PROJECT_ROOT, Settings
from caseflow.database import connect
from caseflow.durable_agent import DurableAgent
from caseflow.mcp_client import MCPTools
from caseflow.tracing import TraceRecorder


def main():
    cfg = Settings.from_env()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["start", "pending", "approve", "reject", "resume"])
    parser.add_argument("--tenant", choices=["northwind", "contoso"], default="northwind")
    parser.add_argument("--ticket-id")
    parser.add_argument("--run-id")
    parser.add_argument(
        "--checkpoint", type=Path, default=PROJECT_ROOT / ".cache/agent-checkpoints.sqlite"
    )
    parser.add_argument("--trace", action="store_true")
    parser.add_argument(
        "--mcp-url", default=os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8003/mcp")
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.action == "start" and not args.ticket_id:
        parser.error("start requires --ticket-id")
    if args.action in {"approve", "reject", "resume"} and not args.run_id:
        parser.error("This command requires --run-id")
    role = "APPROVER" if args.action in {"pending", "approve", "reject"} else "WORKER"
    token = os.getenv(f"{args.tenant.upper()}_{role}_API_TOKEN", "")
    try:
        with connect(cfg) as conn:
            actor = authenticate(conn, token)
            if actor is None or actor.tenant_id != args.tenant:
                raise ValueError("Provision an active local role token")
            store = ApprovalStore(conn)
            if args.action == "pending":
                result = {"pending": store.pending(actor)}
            elif args.action in {"approve", "reject"}:
                store.decide(actor, args.run_id, args.action == "approve")
                result = {"run_id": args.run_id, "decision": args.action}
            else:
                result = None
        if result is None:
            tracer = TraceRecorder()
            if args.trace:
                from langfuse import get_client

                tracer = TraceRecorder(get_client())
            tools = MCPTools(actor, args.mcp_url, token)
            model_cfg = replace(
                cfg,
                llm_provider="openai_compatible",
                llm_base_url="https://api.groq.com/openai/v1",
                llm_model="openai/gpt-oss-20b",
                llm_timeout=60,
            )
            agent = DurableAgent(cfg, GraphModel(model_cfg), tools, args.checkpoint, tracer)
            result = (
                agent.start(args.ticket_id) if args.action == "start" else agent.resume(args.run_id)
            )
        rendered = json.dumps(result, indent=2, default=str)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
    except Exception as exc:
        raise SystemExit(
            f"Workflow failed ({type(exc).__name__}); check local authority and configuration"
        ) from None


if __name__ == "__main__":
    main()
