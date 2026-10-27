"""Provision only existing read-only MCP credential hashes in configured Neon.

Raw values remain in ignored local .env and memory; no cloud environment/config
file or SSM parameter stores these client tokens. Run after release CI passes.
"""

from dataclasses import replace
from urllib.parse import urlparse

from dotenv import dotenv_values

from caseflow.auth import TOKEN_FORMAT, authenticate, hash_token, provision_token
from caseflow.config import PROJECT_ROOT, Settings
from caseflow.database import connect

SCOPES = frozenset({"kb:read", "orders:read", "tickets:read"})


def provision(settings, credentials):
    """Atomic and idempotent. Never broaden, revive or overwrite existing roles."""
    with connect(settings) as conn:
        for tenant in ("northwind", "contoso"):
            token = credentials.get(tenant) or ""
            if not TOKEN_FORMAT.fullmatch(token):
                raise ValueError("Existing MCP read credential required")
            if not conn.execute("SELECT 1 FROM tenants WHERE id=%s", (tenant,)).fetchone():
                raise ValueError("Existing demo tenant required")
            exists = conn.execute(
                "SELECT 1 FROM api_tokens WHERE token_hash=%s", (hash_token(token),)
            ).fetchone()
            if exists:
                actor = authenticate(conn, token)
                if actor is None or actor.tenant_id != tenant or actor.scopes != SCOPES:
                    raise ValueError("Cloud credential differs or is inactive")
            else:
                provision_token(conn, tenant, token, sorted(SCOPES))


def main():
    values = dotenv_values(PROJECT_ROOT / ".env")
    url = values.get("NEON_DATABASE_URL") or ""
    if not (urlparse(url).hostname or "").endswith(".neon.tech"):
        raise ValueError("Expected the configured Neon database")
    provision(
        replace(Settings(), database_url=url),
        {
            tenant: values.get(tenant.upper() + "_MCP_API_TOKEN")
            for tenant in ("northwind", "contoso")
        },
    )
    print({"status": "read_only_hashes_verified", "tenants": 2, "scopes": sorted(SCOPES)})


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(
            f"MCP cloud credentials failed ({type(exc).__name__}); values withheld"
        ) from None
