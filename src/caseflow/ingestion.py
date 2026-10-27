"""Validate a complete Markdown batch, embed it, and replace documents atomically."""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from caseflow.chunking import Chunk, chunk_text
from caseflow.database import KnowledgeStore
from caseflow.embeddings import Embeddings, validate_vector

SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


@dataclass(frozen=True)
class Article:
    id: str
    title: str
    source: str
    text: str


def load_articles(directory: Path) -> list[Article]:
    """Load only direct .md children; tenant identity never comes from article text."""
    if not directory.is_dir():
        raise ValueError("Article directory does not exist")
    paths = sorted(directory.glob("*.md"))
    if not paths:
        raise ValueError("Article directory contains no Markdown files")
    articles = []
    for path in paths:
        if path.is_symlink():
            raise ValueError("Article symlinks are not supported")
        if not SLUG.fullmatch(path.stem):
            raise ValueError("Article filenames must use lowercase letters, digits and hyphens")
        text = path.read_text(encoding="utf-8-sig")
        first_line = text.splitlines()[0] if text else ""
        if not first_line.startswith("# ") or not first_line[2:].strip():
            raise ValueError("Each article must begin with a nonempty Markdown title")
        articles.append(Article(path.stem, first_line[2:].strip(), path.name, text))
    return articles


def ingest_articles(
    store: KnowledgeStore,
    embedder: Embeddings,
    tenant_id: str,
    articles: Sequence[Article],
    chunk_size: int = 800,
    overlap: int = 120,
) -> dict:
    """No deletes outside the supplied documents; failures roll back the entire batch.

    Call this inside a database connection context so its outer transaction commits.
    This is a trusted local admin operation, not an authenticated public endpoint.
    """
    if not tenant_id.strip() or not articles:
        raise ValueError("Provide a tenant and at least one article")
    if embedder.model_name != store.model_name or embedder.dimension != 384:
        raise ValueError("Embedder must match the store model and 384-dimensional schema")
    if len({a.id for a in articles}) != len(articles):
        raise ValueError("Duplicate article ids in one batch")

    prepared: list[tuple[Article, list[Chunk]]] = []
    for article in articles:
        if not SLUG.fullmatch(article.id) or not article.title.strip():
            raise ValueError("Each article needs a valid id and title")
        chunks = chunk_text(article.text, chunk_size, overlap)
        if not chunks:
            raise ValueError("Article text must not be empty")
        prepared.append((article, chunks))

    # Retain article context in later chunks even when the heading is in the first window.
    inputs = [
        f"{article.title}\n\n{chunk.text}" for article, chunks in prepared for chunk in chunks
    ]
    vectors = embedder.embed_documents(inputs)
    if len(vectors) != len(inputs):
        raise ValueError("The embedder returned the wrong number of vectors")
    checked = [validate_vector(vector) for vector in vectors]

    offset = 0
    with store.conn.transaction():
        for article, chunks in prepared:
            count = len(chunks)
            store.put_document(
                tenant_id,
                article.id,
                article.title,
                article.source,
                [chunk.text for chunk in chunks],
                checked[offset : offset + count],
            )
            offset += count
    return {
        "tenant_id": tenant_id,
        "documents": len(articles),
        "chunks": len(vectors),
        "embed_model": embedder.model_name,
        "chunk_size": chunk_size,
        "overlap": overlap,
        "size_unit": "characters",
        "embedding_context": "article-title-prefix",
    }
