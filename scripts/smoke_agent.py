"""Authenticated deployed/local HTTP flow using an isolated synthetic test tenant.

Operator approval is simulated only for this temporary fixture. Never uses or
approves a stored demo/customer request. Cleans its exact random tenant at end.
"""

import argparse
import json
import secrets
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import httpx
from dotenv import dotenv_values
from psycopg.conninfo import conninfo_to_dict

from caseflow.agent_tools import safe_base_url
from caseflow.auth import provision_token
from caseflow.config import LOCAL_DATABASE_URL, PROJECT_ROOT, Settings
from caseflow.database import connect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--database", choices=["local", "neon"], default="local")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base = safe_base_url(args.base_url)
    if args.database == "local":
        url = LOCAL_DATABASE_URL
    else:
        url = dotenv_values(PROJECT_ROOT / ".env").get("NEON_DATABASE_URL") or ""
        if not (conninfo_to_dict(url).get("host") or "").endswith(".neon.tech"):
            raise ValueError("Expected configured Neon endpoint")
    cfg = replace(Settings(), database_url=url)
    tenant = "smoke-" + uuid4().hex
    foreign = tenant + "-foreign"
    worker, operator, other = [secrets.token_urlsafe(32) for _ in range(3)]
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "base_url": base,
        "database": args.database,
        "scope": "isolated synthetic fixture; operator decision simulated; not a demo approval",
        "checks": [],
        "complete": False,
    }
    with connect(cfg) as conn:
        for identity in (tenant, foreign):
            conn.execute("INSERT INTO tenants (id,name) VALUES (%s,'Synthetic smoke')", (identity,))
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
                      VALUES (%s,'smoke-ticket','c1','I want a refund of 75 dollars for order NW-1044.','open')""",
            (tenant,),
        )
        provision_token(
            conn,
            tenant,
            worker,
            [
                "agent:run",
                "kb:read",
                "orders:read",
                "tickets:read",
                "refunds:propose",
                "refunds:execute",
            ],
        )
        provision_token(conn, tenant, operator, ["refund:approve"])
        provision_token(conn, foreign, other, ["agent:run"])
    stage = "health"
    try:
        with httpx.Client(timeout=150, follow_redirects=False) as client:

            def request(method, path, token=None, **kwargs):
                headers = {"Authorization": "Bearer " + token} if token else {}
                return client.request(method, base + path, headers=headers, **kwargs)

            assert request("GET", "/health").status_code == 200
            assert request("GET", "/ready").status_code == 200
            assert request("GET", "/approvals").status_code == 401
            report["checks"].append("health_ready_missing_auth")
            stage = "start"
            response = request("POST", "/runs", worker, json={"ticket_id": "smoke-ticket"})
            assert response.status_code == 200
            paused = response.json()
            assert (
                paused["status"] == "needs_approval"
                and paused["approval_durable"]
                and not paused["refund_executed"]
            )
            run_id = paused["run_id"]
            report["checks"].append("durable_approval_pause")
            stage = "authorization"
            assert request("GET", f"/runs/{run_id}", other).status_code == 403
            assert request("POST", f"/runs/{run_id}/resume", worker).status_code == 403
            assert (
                request(
                    "POST", f"/runs/{run_id}/resume", worker, json={"approved": True}
                ).status_code
                == 422
            )
            assert (
                request(
                    "POST", f"/approvals/{run_id}/decision", worker, json={"approved": True}
                ).status_code
                == 403
            )
            report["checks"].append("tenant_scope_and_forged_resume_blocked")
            stage = "decision"
            assert any(
                r["run_id"] == run_id
                for r in request("GET", "/approvals", operator).json()["pending"]
            )
            assert (
                request(
                    "POST", f"/approvals/{run_id}/decision", operator, json={"approved": True}
                ).status_code
                == 200
            )
            stage = "resume"
            completed = request("POST", f"/runs/{run_id}/resume", worker).json()
            assert completed["status"] == "refunded" and completed["refund_executed"]
            assert request("POST", f"/runs/{run_id}/resume", worker).json()["status"] == "refunded"
            report["checks"].append("simulated_operator_approved_and_resumed")
            with connect(cfg) as conn:
                assert (
                    conn.execute(
                        "SELECT count(*) n FROM refunds WHERE tenant_id=%s", (tenant,)
                    ).fetchone()["n"]
                    == 1
                )
            report["checks"].append("exactly_one_mock_refund_after_retry")
            report["complete"] = True
    except Exception as exc:
        report.update(failed_stage=stage, error_category=type(exc).__name__)
    finally:
        with connect(cfg) as conn:
            for identity in (tenant, foreign):
                for table in ("checkpoint_writes", "checkpoint_blobs", "checkpoints"):
                    conn.execute(f"DELETE FROM {table} WHERE thread_id LIKE %s", (identity + ":%",))
                for table in (
                    "refunds",
                    "refund_approvals",
                    "agent_runs",
                    "tickets",
                    "orders",
                    "customers",
                    "api_tokens",
                ):
                    conn.execute(f"DELETE FROM {table} WHERE tenant_id=%s", (identity,))
                conn.execute("DELETE FROM tenants WHERE id=%s", (identity,))
        report["synthetic_fixture_removed"] = True
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["complete"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
