"""Local bootstrap and a repeatable real-embedding nearest-neighbor check."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import psycopg

from support_copilot.bootstrap import provision_env_token, seed_empty_corpus
from support_copilot.config import PROJECT_ROOT, Settings
from support_copilot.database import KnowledgeStore, connect, migrate
from support_copilot.embeddings import FastEmbedAdapter
from support_copilot.ingestion import ingest_articles, load_articles
from support_copilot.mock_backend import seed_mock

DEMO_DOCUMENTS = [
    (
        "returns-policy",
        "Returns and refunds",
        "Return unused Northwind items with tags within 30 days of delivery. "
        "Start a return through support with your order number. "
        "Refunds go to the original payment method after inspection.",
    ),
    (
        "shipping-policy",
        "Shipping and delivery",
        "Northwind standard shipping takes 3 to 5 business days. "
        "Express delivery takes 1 to 2 business days. Tracking is emailed after dispatch. "
        "Standard shipping is free for orders over 75 dollars.",
    ),
    (
        "order-cancellation",
        "Cancel an order",
        "You may cancel a Northwind order within one hour of purchase if it has not shipped. "
        "Contact support with your order number. A shipped order cannot be cancelled; "
        "follow the returns policy after delivery instead.",
    ),
]

DEMO_QUESTIONS = [
    ("How do I return an item?", "returns-policy"),
    ("How long does standard delivery take?", "shipping-policy"),
    ("Can I cancel an order before it ships?", "order-cancellation"),
    ("Where is the tracking number for my package?", "shipping-policy"),
    ("When do I receive my money back after a return?", "returns-policy"),
]


def bootstrap(settings: Settings) -> dict:
    migrate(settings)
    with connect(settings) as conn:
        for tenant_id, name in [("northwind", "Northwind Outfitters"), ("contoso", "Contoso Gear")]:
            conn.execute(
                "INSERT INTO tenants (id, name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
                (tenant_id, name),
            )
        version = conn.execute(
            "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
        ).fetchone()["extversion"]
    return {"status": "ready", "vector_version": version, "embedding_dimensions": 384}


def check_search(settings: Settings) -> dict:
    bootstrap(settings)
    embedder = FastEmbedAdapter(settings)
    demo_tenant = "northwind-day1-demo"
    # This is the Day 1 three-document experiment; chunking arrives in Day 2.
    vectors = embedder.embed_documents([doc[2] for doc in DEMO_DOCUMENTS])
    with connect(settings) as conn:
        conn.execute(
            "INSERT INTO tenants (id, name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
            (demo_tenant, "Northwind Day 1 isolated experiment"),
        )
        store = KnowledgeStore(conn, embedder.model_name)
        for (doc_id, title, text), vector in zip(DEMO_DOCUMENTS, vectors, strict=True):
            store.put_document(demo_tenant, doc_id, title, "day-1-demo", [text], [vector])
    results = []
    for question, expected in DEMO_QUESTIONS:
        query = embedder.embed_query(question)
        with connect(settings) as conn:
            rows = KnowledgeStore(conn, embedder.model_name).search(demo_tenant, query, top_k=3)
        ids = [row["document_id"] for row in rows]
        results.append(
            {
                "question": question,
                "expected_doc": expected,
                "top_doc": ids[0] if ids else None,
                "expected_rank": ids.index(expected) + 1 if expected in ids else None,
                "results": [
                    {"document_id": r["document_id"], "score": round(r["score"], 4)} for r in rows
                ],
            }
        )
    return {
        "check_kind": "day-1-sanity-check-not-a-retrieval-benchmark",
        "checked_at": datetime.now(UTC).isoformat(),
        "model": embedder.model_name,
        "tenant_id": demo_tenant,
        "dimension": embedder.dimension,
        "corpus_documents": len(DEMO_DOCUMENTS),
        "top1_accuracy": sum(r["top_doc"] == r["expected_doc"] for r in results) / len(results),
        "questions": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "init-db",
            "check-search",
            "ingest",
            "provision-token",
            "seed-corpus",
            "seed-mock",
        ],
    )
    parser.add_argument("--output", type=Path, help="Optionally save the JSON result")
    parser.add_argument("--tenant", help="Explicit trusted-admin tenant for ingestion")
    parser.add_argument("--directory", type=Path, help="Directory of Markdown articles")
    parser.add_argument("--chunk-size", type=int, default=800, help="Chunk size in characters")
    parser.add_argument("--overlap", type=int, default=120, help="Overlap in characters")
    parser.add_argument(
        "--scope", action="append", default=[], help="Token scope; repeat for multiple scopes"
    )
    parser.add_argument("--env-name", help="Name of a new token setting in the ignored .env")
    args = parser.parse_args()
    settings = Settings.from_env()
    try:
        if args.command == "init-db":
            result = bootstrap(settings)
        elif args.command == "check-search":
            result = check_search(settings)
        elif args.command == "seed-mock":
            bootstrap(settings)
            result = seed_mock(settings, PROJECT_ROOT / "data/mock/entities.json")
        elif args.command == "seed-corpus":
            bootstrap(settings)
            result = seed_empty_corpus(settings, PROJECT_ROOT / "data")
        elif args.command == "provision-token":
            if not args.tenant or not args.scope or not args.env_name:
                parser.error("provision-token requires --tenant, --scope and --env-name")
            result = provision_env_token(
                settings, args.tenant, args.scope, args.env_name, PROJECT_ROOT / ".env"
            )
        else:
            if not args.tenant or not args.directory:
                parser.error("ingest requires --tenant and --directory")
            articles = load_articles(args.directory)
            embedder = FastEmbedAdapter(settings)
            with connect(settings) as conn:
                result = ingest_articles(
                    KnowledgeStore(conn, embedder.model_name),
                    embedder,
                    args.tenant,
                    articles,
                    args.chunk_size,
                    args.overlap,
                )
    except ValueError as exc:
        parser.exit(1, f"Invalid input: {exc}\n")
    except psycopg.Error:
        # Driver errors can contain connection credentials; keep the CLI error generic.
        parser.exit(1, "Database operation failed. Check Docker, DATABASE_URL and the schema.\n")
    output = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
