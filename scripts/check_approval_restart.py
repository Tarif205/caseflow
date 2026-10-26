"""Isolated restart test: synthetic actors/approval in loopback copilot_test only.

This test's simulated operator decisions are not approval of a real/demo ticket.
Children exit between start and resume; the random test tenant is removed at end.
"""

import argparse
import json
import os
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

from psycopg.conninfo import conninfo_to_dict

from support_copilot.approvals import ApprovalStore
from support_copilot.auth import authenticate, provision_token
from support_copilot.config import Settings
from support_copilot.database import connect, migrate
from support_copilot.durable_agent import DurableAgent, setup_postgres_checkpoints
from support_copilot.mock_backend import MockStore


def settings():
    url = os.environ["TEST_DATABASE_URL"]
    info = conninfo_to_dict(url)
    if (
        info.get("host") not in {"localhost", "127.0.0.1", "::1"}
        or info.get("dbname") != "copilot_test"
    ):
        raise ValueError("Only loopback copilot_test is allowed")
    return Settings(database_url=url)


class FixtureModel:
    def __init__(self, fail=False):
        self.fail = fail

    def complete_json(self, messages, schema, timeout):
        if self.fail:
            raise AssertionError("Resume must not rerun a model")
        return schema.model_validate(
            {"intent": "refund", "order_id": "NW-1044", "amount_cents": 7500}
            if schema.__name__ == "Intake"
            else {"action": "refund"}
        )


class FixtureTools:
    def __init__(self, cfg, actor):
        self.cfg, self.principal = cfg, actor

    def execute(self, name, args, timeout):
        assert name == "get_order"
        with connect(self.cfg) as conn:
            return MockStore(conn).get_order(self.principal.tenant_id, args["order_id"])


def child(phase, checkpoint, run_id):
    cfg = settings()
    with connect(cfg) as conn:
        actor = authenticate(conn, os.environ["RESTART_TEST_TOKEN"])
    if actor is None:
        raise ValueError("Synthetic actor missing")
    agent = DurableAgent(
        cfg,
        FixtureModel(fail=phase == "resume"),
        FixtureTools(cfg, actor),
        checkpoint,
        checkpoint_backend=os.getenv("RESTART_CHECKPOINT_BACKEND", "sqlite"),
    )
    return agent.start("t1") if phase == "start" else agent.resume(run_id)


def verify(checkpoint_backend="sqlite"):
    cfg = settings()
    migrate(cfg)
    if checkpoint_backend == "postgres":
        setup_postgres_checkpoints(cfg)
    tenant = "test-restart-" + uuid4().hex
    worker, operator = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    with connect(cfg) as conn:
        conn.execute("INSERT INTO tenants (id,name) VALUES (%s,'Restart test')", (tenant,))
        conn.execute(
            "INSERT INTO customers (tenant_id,id,name) VALUES (%s,'c1','Synthetic')", (tenant,)
        )
        conn.execute(
            """INSERT INTO orders (tenant_id,id,customer_id,status,total_cents,currency,placed_on)
                      VALUES (%s,'NW-1044','c1','delivered',7500,'USD','2026-10-20')""",
            (tenant,),
        )
        conn.execute(
            """INSERT INTO tickets (tenant_id,id,customer_id,text,status)
                      VALUES (%s,'t1','c1','Refund NW-1044 for 75 dollars','open')""",
            (tenant,),
        )
        provision_token(
            conn,
            tenant,
            worker,
            ["agent:run", "tickets:read", "orders:read", "refunds:propose", "refunds:execute"],
        )
        provision_token(conn, tenant, operator, ["refund:approve"])
    try:
        env = {
            **os.environ,
            "RESTART_TEST_TOKEN": worker,
            "RESTART_CHECKPOINT_BACKEND": checkpoint_backend,
        }
        with tempfile.TemporaryDirectory(prefix="copilot-approval-") as directory:
            checkpoint = Path(directory) / "checkpoints.sqlite"

            def invoke(phase, run_id=None):
                command = [
                    sys.executable,
                    __file__,
                    "--phase",
                    phase,
                    "--checkpoint",
                    str(checkpoint),
                ]
                if run_id:
                    command += ["--run-id", run_id]
                completed = subprocess.run(
                    command, env=env, capture_output=True, text=True, timeout=45
                )
                if completed.returncode:
                    raise RuntimeError("Restart child failed; raw stderr withheld")
                return json.loads(completed.stdout)

            first = invoke("start")
            assert first["status"] == "needs_approval" and first["approval_durable"]
            run_id = first["run_id"]
            with connect(cfg) as conn:
                ledger = ApprovalStore(conn)
                approver = authenticate(conn, operator)
                actor = authenticate(conn, worker)
                assert len(ledger.pending(approver)) == 1
                # Confirm that merely knowing the run id cannot execute it.
                from support_copilot.approvals import ApprovalDenied

                try:
                    ledger.execute(actor, run_id)
                except ApprovalDenied:
                    pass
                else:
                    raise AssertionError("Unapproved execution succeeded")
                ledger.decide(approver, run_id, True)
            second = invoke("resume", run_id)
            assert second["status"] == "refunded" and second["refund_executed"]
            third = invoke("resume", run_id)
            assert third["status"] == "refunded"
            with connect(cfg) as conn:
                assert (
                    conn.execute(
                        "SELECT count(*) n FROM refunds WHERE tenant_id=%s", (tenant,)
                    ).fetchone()["n"]
                    == 1
                )
            return {
                "process_exit_between_start_and_resume": True,
                "durable_pause": True,
                "unapproved_execution_blocked": True,
                "simulated_human_approval": True,
                "resume_without_model_replay": True,
                "refund_rows_after_repeated_resume": 1,
                "checkpoint_backend": checkpoint_backend,
                "scope": "isolated synthetic tenant in loopback copilot_test; not a demo approval",
            }
    finally:
        with connect(cfg) as conn:
            if checkpoint_backend == "postgres":
                for table in ("checkpoint_writes", "checkpoint_blobs", "checkpoints"):
                    conn.execute(f"DELETE FROM {table} WHERE thread_id LIKE %s", (tenant + ":%",))
            # Exact random test-tenant match only; never touch seeded demo/cloud rows.
            for table in (
                "refunds",
                "refund_approvals",
                "agent_runs",
                "tickets",
                "orders",
                "customers",
                "api_tokens",
            ):
                conn.execute(f"DELETE FROM {table} WHERE tenant_id=%s", (tenant,))
            conn.execute("DELETE FROM tenants WHERE id=%s", (tenant,))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["start", "resume"])
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--checkpoint-backend", choices=["sqlite", "postgres"], default="sqlite")
    args = parser.parse_args()
    try:
        result = (
            child(args.phase, args.checkpoint, args.run_id)
            if args.phase
            else verify(args.checkpoint_backend)
        )
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result))
    except Exception as exc:
        raise SystemExit(
            f"Restart verification failed ({type(exc).__name__}); raw details withheld"
        ) from None


if __name__ == "__main__":
    main()
