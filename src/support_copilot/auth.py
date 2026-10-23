"""High-entropy bearer tokens are stored as SHA256 hashes, never plaintext."""

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime

import psycopg

TOKEN_FORMAT = re.compile(r"[A-Za-z0-9_-]{32,128}")
KNOWN_SCOPES = {"kb:read", "kb:write", "orders:read", "tickets:read", "agent:run", "refund:approve"}


@dataclass(frozen=True)
class Principal:
    tenant_id: str
    scopes: frozenset[str]
    token_hash: str = field(repr=False)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def authenticate(conn: psycopg.Connection, token: str) -> Principal | None:
    if not TOKEN_FORMAT.fullmatch(token):
        return None
    digest = hash_token(token)
    row = conn.execute(
        """SELECT tenant_id, scopes FROM api_tokens
           WHERE token_hash = %s AND revoked_at IS NULL
           AND (expires_at IS NULL OR expires_at > now())""",
        (digest,),
    ).fetchone()
    return Principal(row["tenant_id"], frozenset(row["scopes"]), digest) if row else None


def provision_token(
    conn: psycopg.Connection,
    tenant: str,
    token: str,
    scopes: list[str],
    expires_at: datetime | None = None,
) -> None:
    if not TOKEN_FORMAT.fullmatch(token) or not scopes or not set(scopes) <= KNOWN_SCOPES:
        raise ValueError("Provide a high-entropy token and known nonempty scopes")
    conn.execute(
        """INSERT INTO api_tokens (token_hash, tenant_id, scopes, expires_at)
           VALUES (%s, %s, %s, %s)""",
        (hash_token(token), tenant, sorted(set(scopes)), expires_at),
    )
