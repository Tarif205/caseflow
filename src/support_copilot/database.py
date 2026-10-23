"""Postgres connections and raw SQL retrieval, always scoped to a tenant."""

from collections.abc import Sequence
from contextlib import contextmanager
from importlib.resources import files
from uuid import NAMESPACE_URL, uuid5

import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from support_copilot.config import Settings
from support_copilot.embeddings import validate_vector


class EmbeddingModelMismatch(ValueError):
    """Stored data and the configured model must agree before retrieval."""


def migrate(settings: Settings) -> None:
    schema = files("support_copilot").joinpath("schema.sql").read_text(encoding="utf-8")
    with psycopg.connect(settings.database_url, connect_timeout=5) as conn:
        conn.execute(schema)


@contextmanager
def connect(settings: Settings):
    with psycopg.connect(
        settings.database_url,
        row_factory=dict_row,
        connect_timeout=5,
        options="-c statement_timeout=10000",
    ) as conn:
        register_vector(conn)
        yield conn


class KnowledgeStore:
    def __init__(self, conn: psycopg.Connection, model_name: str):
        self.conn = conn
        self.model_name = model_name

    def put_document(
        self,
        tenant_id: str,
        document_id: str,
        title: str,
        source: str,
        texts: Sequence[str],
        vectors: Sequence[Sequence[float]],
    ) -> int:
        if not texts or len(texts) != len(vectors) or any(not t.strip() for t in texts):
            raise ValueError("Provide one nonempty text per vector")
        checked = [validate_vector(vector) for vector in vectors]
        if not tenant_id.strip() or not document_id.strip():
            raise ValueError("Tenant and document id are required")

        # The savepoint keeps an existing document intact if replacement fails.
        with self.conn.transaction():
            self.conn.execute(
                """INSERT INTO documents (tenant_id, id, title, source)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (tenant_id, id) DO UPDATE
                   SET title = EXCLUDED.title, source = EXCLUDED.source, updated_at = now()""",
                (tenant_id, document_id, title, source),
            )
            self.conn.execute(
                "DELETE FROM chunks WHERE tenant_id = %s AND document_id = %s",
                (tenant_id, document_id),
            )
            for position, (text, vector) in enumerate(zip(texts, checked, strict=True)):
                chunk_id = uuid5(NAMESPACE_URL, f"{tenant_id}/{document_id}/{position}")
                self.conn.execute(
                    """INSERT INTO chunks
                       (tenant_id, id, document_id, position, text, embedding, embed_model)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (
                        tenant_id,
                        chunk_id,
                        document_id,
                        position,
                        text,
                        np.asarray(vector, dtype=np.float32),
                        self.model_name,
                    ),
                )
        return len(texts)

    def search(self, tenant_id: str, vector: Sequence[float], top_k: int = 5) -> list[dict]:
        if (
            not tenant_id.strip()
            or not isinstance(top_k, int)
            or isinstance(top_k, bool)
            or not 1 <= top_k <= 20
        ):
            raise ValueError("Provide a tenant and a top_k between 1 and 20")
        checked = np.asarray(validate_vector(vector), dtype=np.float32)
        mismatch = self.conn.execute(
            "SELECT 1 FROM chunks WHERE tenant_id = %s AND embed_model <> %s LIMIT 1",
            (tenant_id, self.model_name),
        ).fetchone()
        if mismatch:
            raise EmbeddingModelMismatch(
                "Re-embed this tenant's documents with the configured model"
            )

        rows = self.conn.execute(
            """SELECT c.id, c.document_id, c.position, c.text, d.title, d.source,
                      1 - (c.embedding <=> %s) AS score
               FROM chunks c
               JOIN documents d ON d.tenant_id = c.tenant_id AND d.id = c.document_id
               WHERE c.tenant_id = %s AND c.embed_model = %s
               ORDER BY c.embedding <=> %s, c.id
               LIMIT %s""",
            (checked, tenant_id, self.model_name, checked, top_k),
        ).fetchall()
        return [{**row, "id": str(row["id"])} for row in rows]
