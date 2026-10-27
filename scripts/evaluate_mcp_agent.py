"""25 live-model MCP scenarios with a direct-read replay control; no action writes."""

import argparse
import hashlib
import json
import secrets
import time
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from psycopg.conninfo import conninfo_to_dict

from caseflow.agent_evaluation import dataset_hash, judge, load_scenarios
from caseflow.agent_graph import GraphModel, run_graph
from caseflow.agent_tools import RecordNotFound, ToolFailure
from caseflow.auth import authenticate, provision_token
from caseflow.config import PROJECT_ROOT, Settings
from caseflow.database import connect
from caseflow.mcp_client import NAMES, MCPTools
from caseflow.mcp_server import MCPReads, ReadFailure
from caseflow.mock_backend import Fixtures


@contextmanager
def isolated_fixtures(cfg):
    info = conninfo_to_dict(cfg.database_url)
    if info.get("host") not in {"localhost", "127.0.0.1", "::1"} or info.get("dbname") != "copilot":
        raise ValueError("Only the local development database is allowed")
    prefix = "eval13-" + uuid4().hex
    credentials = {}
    data = Fixtures.model_validate_json((PROJECT_ROOT / "data/mock/entities.json").read_text())
    try:
        with connect(cfg) as conn:
            for tenant in ("northwind", "contoso"):
                alias, token = prefix + "-" + tenant, secrets.token_urlsafe(32)
                conn.execute(
                    "INSERT INTO tenants (id,name) VALUES (%s,'Synthetic MCP evaluation')", (alias,)
                )
                conn.execute(
                    "INSERT INTO documents (tenant_id,id,title,source) SELECT %s,id,title,source FROM documents WHERE tenant_id=%s",
                    (alias, tenant),
                )
                conn.execute(
                    """INSERT INTO chunks (tenant_id,id,document_id,position,text,embedding,embed_model)
                       SELECT %s,id,document_id,position,text,embedding,embed_model FROM chunks WHERE tenant_id=%s""",
                    (alias, tenant),
                )
                assert (
                    conn.execute(
                        "SELECT count(*) n FROM chunks WHERE tenant_id=%s", (alias,)
                    ).fetchone()["n"]
                    > 0
                )
                for c in data.customers:
                    if c.tenant_id == tenant:
                        conn.execute(
                            "INSERT INTO customers (tenant_id,id,name) VALUES (%s,%s,%s)",
                            (alias, c.id, c.name),
                        )
                for o in data.orders:
                    if o.tenant_id == tenant:
                        conn.execute(
                            """INSERT INTO orders (tenant_id,id,customer_id,status,total_cents,currency,tracking_number,placed_on)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                            (
                                alias,
                                o.id,
                                o.customer_id,
                                o.status,
                                o.total_cents,
                                o.currency,
                                o.tracking_number,
                                o.placed_on,
                            ),
                        )
                provision_token(
                    conn,
                    alias,
                    token,
                    ["agent:run", "kb:read", "orders:read", "tickets:read", "refunds:propose"],
                )
                credentials[tenant] = (alias, token)
        yield credentials
    finally:
        with connect(cfg) as conn:
            for tenant in ("northwind", "contoso"):
                alias = prefix + "-" + tenant
                # Exact newly generated namespaces only; demo/approval records untouched.
                for table in ("api_tokens", "orders", "customers", "chunks", "documents"):
                    conn.execute(f"DELETE FROM {table} WHERE tenant_id=%s", (alias,))
                conn.execute("DELETE FROM tenants WHERE id=%s", (alias,))


class DirectReads:
    def __init__(self, principal, reads):
        self.principal, self.reads = principal, reads

    def execute(self, name, arguments, timeout):
        try:
            return self.reads.call(NAMES[name], arguments)
        except ReadFailure as exc:
            if exc.code == "not_found":
                raise RecordNotFound("Record not found") from None
            raise ToolFailure("Read unavailable") from None


class Decisions:
    def __init__(self, model=None, recorded=None):
        self.model, self.recorded, self.position = (
            model,
            recorded if recorded is not None else [],
            0,
        )

    def complete_json(self, messages, schema, timeout):
        digest = hashlib.sha256(json.dumps(messages, sort_keys=True).encode()).hexdigest()
        if self.model is not None:
            value = self.model.complete_json(messages, schema, timeout)
            self.recorded.append((digest, schema.__name__, value.model_dump()))
            return value
        expected, name, value = self.recorded[self.position]
        self.position += 1
        if expected != digest or name != schema.__name__:
            raise ValueError("Direct/MCP model input differs")
        return schema.model_validate(value)


def comparable(result):
    return {k: v for k, v in result.items() if k not in {"elapsed_seconds", "diagnostic"}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mcp-url", default="http://127.0.0.1:8003/mcp")
    parser.add_argument(
        "--output", type=Path, default=PROJECT_ROOT / "evals/results/day-13-agent-mcp.json"
    )
    parser.add_argument("--pause-seconds", type=float, default=4)
    args = parser.parse_args()
    if not 0 <= args.pause_seconds <= 60:
        parser.error("Pause must be 0 through 60 seconds")
    cfg = replace(
        Settings.from_env(),
        llm_provider="openai_compatible",
        llm_model="openai/gpt-oss-20b",
        llm_base_url="https://api.groq.com/openai/v1",
        llm_timeout=60,
    )
    path = PROJECT_ROOT / "evals/agent/scenarios.jsonl"
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "dataset_sha256": dataset_hash(path),
        "order_fixture_sha256": dataset_hash(PROJECT_ROOT / "data/mock/entities.json"),
        "model": cfg.llm_model,
        "scope": "Live hosted MCP run; direct control replays identical model decisions, not independent inference. Isolated local immutable orders. Approval placeholder only; no refunds.",
        "mcp_url": args.mcp_url,
        "results": [],
        "complete": False,
    }
    model = GraphModel(cfg)
    try:
        with isolated_fixtures(cfg) as credentials:
            for scenario in load_scenarios(path):
                alias, token = credentials[scenario.tenant]
                with connect(cfg, read_only=True) as conn:
                    principal = authenticate(conn, token)
                assert principal is not None and principal.tenant_id == alias
                decisions = Decisions(model)
                result = run_graph(
                    scenario.ticket,
                    decisions,
                    MCPTools(principal, args.mcp_url, token),
                    customer_id=scenario.customer_id,
                )
                # Infrastructure failures must be counted, never converted into a success.
                replay = Decisions(recorded=decisions.recorded)
                control = run_graph(
                    scenario.ticket,
                    replay,
                    DirectReads(principal, MCPReads(cfg, token)),
                    customer_id=scenario.customer_id,
                )
                parity = comparable(result) == comparable(control) and replay.position == len(
                    replay.recorded
                )
                passed = judge(scenario, result, PROJECT_ROOT / "data", approval_placeholder=True)
                direct_passed = judge(
                    scenario, control, PROJECT_ROOT / "data", approval_placeholder=True
                )
                report["results"].append(
                    {
                        "id": scenario.id,
                        "passed": passed,
                        "direct_replay_passed": direct_passed,
                        "parity": parity,
                        "result": result,
                    }
                )
                report.update(
                    scenarios=len(report["results"]),
                    passed=sum(r["passed"] for r in report["results"]),
                    direct_replay_passed=sum(r["direct_replay_passed"] for r in report["results"]),
                    parity_cases=sum(r["parity"] for r in report["results"]),
                    rate_limit_retries=model.retry_count,
                )
                report["success_rate"] = report["passed"] / report["scenarios"]
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(
                    json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8"
                )
                print(
                    json.dumps(
                        {
                            "id": scenario.id,
                            "passed": passed,
                            "parity": parity,
                            "reason": result["reason"],
                        }
                    ),
                    flush=True,
                )
                time.sleep(args.pause_seconds)
            report["complete"] = report["scenarios"] == 25
    finally:
        report["synthetic_fixture_removed"] = True
        args.output.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(
            f"MCP evaluation failed ({type(exc).__name__}); raw details withheld"
        ) from None
