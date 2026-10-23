"""Repeat the real corpus import and inspect actual row counts and stable chunk ids.

This is an integration check of ingestion, not a retrieval-quality evaluation.
It uses only the local development database; it refuses a remote or non-demo DB.
"""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import psycopg
from psycopg.conninfo import conninfo_to_dict

from support_copilot.cli import bootstrap
from support_copilot.config import PROJECT_ROOT, Settings
from support_copilot.database import KnowledgeStore, connect
from support_copilot.embeddings import FastEmbedAdapter
from support_copilot.ingestion import ingest_articles, load_articles


def snapshot(settings: Settings, tenant: str) -> dict:
    with connect(settings) as conn:
        rows = conn.execute(
            """SELECT document_id, id, position, text FROM chunks
               WHERE tenant_id = %s ORDER BY document_id, position""",
            (tenant,),
        ).fetchall()
        documents = conn.execute(
            "SELECT count(*) AS n FROM documents WHERE tenant_id = %s", (tenant,)
        ).fetchone()["n"]
    payload = json.dumps([{**row, "id": str(row["id"])} for row in rows], sort_keys=True).encode()
    return {
        "documents": documents,
        "chunks": len(rows),
        "chunk_content_sha256": hashlib.sha256(payload).hexdigest(),
    }


def check(settings: Settings) -> dict:
    target = conninfo_to_dict(settings.database_url)
    if (
        target.get("host") not in {"localhost", "127.0.0.1", "::1"}
        or target.get("dbname") != "copilot"
    ):
        raise ValueError("This corpus check requires the local copilot development database")
    bootstrap(settings)
    embedder = FastEmbedAdapter(settings)
    corpora = {
        tenant: load_articles(PROJECT_ROOT / "data" / tenant) for tenant in ("northwind", "contoso")
    }
    passes = []
    for _ in range(2):
        imported = {}
        for tenant, articles in corpora.items():
            with connect(settings) as conn:
                imported[tenant] = ingest_articles(
                    KnowledgeStore(conn, embedder.model_name), embedder, tenant, articles
                )
            stored = snapshot(settings, tenant)
            if (stored["documents"], stored["chunks"]) != (
                len(articles),
                imported[tenant]["chunks"],
            ):
                raise RuntimeError("Stored counts do not match this corpus; inspect extra data")
            imported[tenant]["stored"] = stored
        passes.append(imported)
    if passes[0] != passes[1]:
        raise RuntimeError("Re-ingestion changed chunk contents, ids or row counts")

    checks = []
    question = "Contoso returns unused items within 60 days. What is the return policy?"
    query_vector = embedder.embed_query(question)
    for tenant in corpora:
        with connect(settings) as conn:
            rows = KnowledgeStore(conn, embedder.model_name).search(tenant, query_vector, 20)
        expected_texts = {article.id: article.text for article in corpora[tenant]}
        if not rows or any(
            row["document_id"] not in expected_texts
            or row["text"] not in expected_texts[row["document_id"]]
            for row in rows
        ):
            raise RuntimeError("Search returned text outside the requested tenant corpus")
        checks.append(
            {
                "tenant_id": tenant,
                "query": question,
                "hits_checked": len(rows),
                "all_hits_belong_to_requested_tenant": True,
            }
        )
    return {
        "checked_at": datetime.now(UTC).isoformat(),
        "check_kind": "real-embedding-ingestion-idempotency-and-isolation",
        "model": embedder.model_name,
        "passes": passes,
        "repeat_import_identical": True,
        "tenant_checks": checks,
        "limitations": "Not a retrieval accuracy benchmark; fixtures and labels are synthetic.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = check(Settings.from_env())
    except psycopg.Error:
        parser.exit(1, "Database check failed. Verify local Docker and database settings.\n")
    except (ValueError, RuntimeError) as exc:
        parser.exit(1, f"Ingestion check failed: {exc}\n")
    payload = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
