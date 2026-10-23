"""Trusted operator helpers. Tokens are written only to the ignored .env."""

import re
import secrets
from pathlib import Path

from dotenv import dotenv_values

from support_copilot.auth import authenticate, hash_token, provision_token
from support_copilot.config import Settings
from support_copilot.database import KnowledgeStore, connect
from support_copilot.embeddings import FastEmbedAdapter
from support_copilot.ingestion import ingest_articles, load_articles


def provision_env_token(
    settings: Settings, tenant: str, scopes: list[str], name: str, path: Path
) -> dict:
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*_API_TOKEN", name):
        raise ValueError("Token setting name must be uppercase and end in _API_TOKEN")
    existing = dotenv_values(path).get(name) if path.exists() else None
    # A configured empty placeholder is not silently replaced: appending a duplicate
    # would make settings ambiguous. Pick a new setting name or edit the empty line.
    if existing is not None and not existing.strip():
        raise ValueError("Remove the empty token placeholder or use a new setting name")
    token = existing or secrets.token_urlsafe(32)
    with connect(settings) as conn:
        row = conn.execute(
            "SELECT tenant_id, scopes FROM api_tokens WHERE token_hash = %s", (hash_token(token),)
        ).fetchone()
        if row:
            principal = authenticate(conn, token)
            if (
                principal is None
                or principal.tenant_id != tenant
                or principal.scopes != frozenset(scopes)
            ):
                raise ValueError(
                    "Existing token metadata differs or is inactive; use a new setting name"
                )
        else:
            provision_token(conn, tenant, token, scopes)
        if not existing:
            # Append a newly generated value. Do not copy or rewrite other secret values.
            with path.open("a", encoding="utf-8") as handle:
                handle.write(f"\n{name}={token}\n")
    return {
        "status": "provisioned",
        "tenant_id": tenant,
        "scopes": sorted(set(scopes)),
        "setting": name,
    }


def seed_empty_corpus(settings: Settings, root: Path) -> dict:
    embedder = FastEmbedAdapter(settings)
    results = {}
    for tenant in ("northwind", "contoso"):
        with connect(settings) as conn:
            # Serialize first-time seeds across service restarts without replacing
            # existing API-managed articles.
            conn.execute("SELECT pg_advisory_xact_lock(22042026)")
            count = conn.execute(
                "SELECT count(*) AS n FROM documents WHERE tenant_id = %s", (tenant,)
            ).fetchone()["n"]
            if count:
                results[tenant] = {"status": "kept_existing", "documents": count}
            else:
                results[tenant] = ingest_articles(
                    KnowledgeStore(conn, embedder.model_name),
                    embedder,
                    tenant,
                    load_articles(root / tenant),
                    settings.chunk_size,
                    settings.chunk_overlap,
                )
    return results
