"""Explicit trusted admin: initialize only the configured Neon demo and role hashes.

Run after reviewing/committing the release. Never prints or copies secret values.
"""

from dataclasses import replace
from urllib.parse import urlparse

from dotenv import dotenv_values

from caseflow.auth import authenticate, hash_token, provision_token
from caseflow.cli import bootstrap
from caseflow.config import PROJECT_ROOT, Settings
from caseflow.database import connect
from caseflow.durable_agent import setup_postgres_checkpoints
from caseflow.mock_backend import seed_mock


def main():
    values = dotenv_values(PROJECT_ROOT / ".env")
    url = values.get("NEON_DATABASE_URL") or ""
    host = urlparse(url).hostname or ""
    if not host.endswith(".neon.tech"):
        raise ValueError("Expected configured Neon endpoint")
    cfg = replace(Settings(), database_url=url)
    bootstrap(cfg)
    setup_postgres_checkpoints(cfg)
    seed_mock(cfg, PROJECT_ROOT / "data/mock/entities.json")
    for role, scopes in [
        (
            "WORKER",
            [
                "kb:read",
                "orders:read",
                "tickets:read",
                "agent:run",
                "refunds:propose",
                "refunds:execute",
            ],
        ),
        ("APPROVER", ["refund:approve"]),
    ]:
        token = values.get("NORTHWIND_" + role + "_API_TOKEN") or ""
        if not token:
            raise ValueError("Local role token missing")
        with connect(cfg) as conn:
            existing = conn.execute(
                "SELECT 1 FROM api_tokens WHERE token_hash=%s", (hash_token(token),)
            ).fetchone()
            if existing:
                actor = authenticate(conn, token)
                if (
                    actor is None
                    or actor.tenant_id != "northwind"
                    or actor.scopes != frozenset(scopes)
                ):
                    raise ValueError("Existing cloud role differs or is inactive")
            else:
                provision_token(conn, "northwind", token, scopes)
        print({"role": role, "status": "hash_provisioned"})


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(
            f"Cloud setup failed ({type(exc).__name__}); credentials withheld"
        ) from None
