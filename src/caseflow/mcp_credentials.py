"""Trusted admin provisioning of existing MCP read-token hashes, never tool-exposed."""

from caseflow.auth import TOKEN_FORMAT, authenticate, hash_token, provision_token
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
