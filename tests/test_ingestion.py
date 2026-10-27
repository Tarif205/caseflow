import json
from contextlib import contextmanager
from pathlib import Path

import pytest

from caseflow.config import Settings
from caseflow.database import KnowledgeStore
from caseflow.ingestion import Article, ingest_articles, load_articles

ROOT = Path(__file__).resolve().parents[1]
VECTOR = [1.0] + [0.0] * 383


class FakeEmbeddings:
    model_name = "test-model"
    dimension = 384

    def __init__(self):
        self.inputs = []

    def embed_documents(self, texts):
        self.inputs.extend(texts)
        return [VECTOR for _ in texts]


def article(doc_id="returns", text="A small policy article."):
    return Article(doc_id, "Returns title", f"{doc_id}.md", text)


def test_article_loading_is_sorted_and_uses_filenames_as_ids(tmp_path):
    (tmp_path / "z-last.md").write_text("# Last title\n\nContent.", encoding="utf-8")
    (tmp_path / "a-first.md").write_text("\ufeff# First title\n\nContent.", encoding="utf-8")
    (tmp_path / "ignore.txt").write_text("Not an article", encoding="utf-8")
    articles = load_articles(tmp_path)
    assert [a.id for a in articles] == ["a-first", "z-last"]
    assert articles[0].title == "First title"
    assert articles[0].source == "a-first.md"


@pytest.mark.parametrize("contents", ["", "Missing title", "# \n", "## Wrong level"])
def test_missing_markdown_title_rejected(tmp_path, contents):
    (tmp_path / "article.md").write_text(contents, encoding="utf-8")
    with pytest.raises(ValueError, match="title"):
        load_articles(tmp_path)


def test_empty_directory_and_bad_filenames_rejected(tmp_path):
    with pytest.raises(ValueError, match="no Markdown"):
        load_articles(tmp_path)
    (tmp_path / "Upper Case.md").write_text("# Title\nBody", encoding="utf-8")
    with pytest.raises(ValueError, match="filenames"):
        load_articles(tmp_path)


def test_symlink_article_rejected(tmp_path, monkeypatch):
    (tmp_path / "article.md").write_text("# Title\nBody", encoding="utf-8")
    # No Windows symlink privilege is required to exercise the rejection branch.
    monkeypatch.setattr(Path, "is_symlink", lambda self: True)
    with pytest.raises(ValueError, match="symlinks"):
        load_articles(tmp_path)


def test_corpus_and_candidate_labels_are_well_formed():
    northwind = load_articles(ROOT / "data/northwind")
    contoso = load_articles(ROOT / "data/contoso")
    assert len(northwind) == 15
    assert len(contoso) == 3
    assert {a.id for a in contoso} <= {a.id for a in northwind}
    records = [
        json.loads(line)
        for line in (ROOT / "evals/retrieval/questions.jsonl").read_text().splitlines()
    ]
    assert len(records) == 50
    assert sum(r["answerable"] for r in records) == 40
    assert len({r["id"] for r in records}) == len(records)
    for record in records:
        assert record["tenant"] == "northwind"
        if record["answerable"]:
            assert record["expected_doc"] in {a.id for a in northwind}
        else:
            assert record["expected_doc"] is None
        assert record["question"].strip()


@pytest.mark.integration
class TestDatabaseIngestion:
    def test_reingest_has_same_counts_and_stable_citation_ids(self, db):
        store, (tenant, _) = db
        embedder = FakeEmbeddings()
        docs = [article("first", "x" * 100), article("second", "y" * 80)]
        first = ingest_articles(store, embedder, tenant, docs, 40, 10)
        ids_before = sorted(row["id"] for row in store.search(tenant, VECTOR, 20))
        second = ingest_articles(store, embedder, tenant, docs, 40, 10)
        ids_after = sorted(row["id"] for row in store.search(tenant, VECTOR, 20))
        assert first == second
        assert first["documents"] == 2
        assert first["chunks"] == 6
        assert ids_before == ids_after
        assert embedder.inputs[0].startswith("Returns title\n\n")

    def test_new_chunk_size_removes_old_chunks_and_keeps_unsupplied_documents(self, db):
        store, (tenant, _) = db
        docs = [article("first", "x" * 100), article("second", "keep me")]
        ingest_articles(store, FakeEmbeddings(), tenant, docs, 40, 10)
        ingest_articles(store, FakeEmbeddings(), tenant, [docs[0]], 200, 0)
        rows = store.search(tenant, VECTOR, 20)
        assert len(rows) == 2
        assert {r["document_id"] for r in rows} == {"first", "second"}

    def test_shared_article_id_is_isolated_when_other_tenant_is_reimported(self, db):
        store, (tenant_a, tenant_b) = db
        ingest_articles(store, FakeEmbeddings(), tenant_a, [article(text="Northwind only")])
        ingest_articles(store, FakeEmbeddings(), tenant_b, [article(text="Contoso private")])
        ingest_articles(store, FakeEmbeddings(), tenant_b, [article(text="Contoso updated")])
        assert [r["text"] for r in store.search(tenant_a, VECTOR)] == ["Northwind only"]
        assert [r["text"] for r in store.search(tenant_b, VECTOR)] == ["Contoso updated"]

    def test_embedding_failure_does_not_change_existing_data(self, db):
        store, (tenant, _) = db
        ingest_articles(store, FakeEmbeddings(), tenant, [article(text="Original")])

        class BrokenEmbedder(FakeEmbeddings):
            def embed_documents(self, texts):
                raise RuntimeError("Simulated model failure")

        with pytest.raises(RuntimeError):
            ingest_articles(store, BrokenEmbedder(), tenant, [article(text="Replacement")])
        assert store.search(tenant, VECTOR)[0]["text"] == "Original"

    def test_later_storage_failure_rolls_back_entire_batch(self, db, monkeypatch):
        store, (tenant, _) = db
        ingest_articles(store, FakeEmbeddings(), tenant, [article("first", "Original")])
        original_put = store.put_document

        def fail_on_second(tenant_id, doc_id, *args):
            if doc_id == "second":
                raise RuntimeError("Simulated storage failure after the first replacement")
            return original_put(tenant_id, doc_id, *args)

        monkeypatch.setattr(store, "put_document", fail_on_second)
        with pytest.raises(RuntimeError):
            ingest_articles(
                store,
                FakeEmbeddings(),
                tenant,
                [article("first", "Replacement"), article("second", "New")],
            )
        assert [r["text"] for r in store.search(tenant, VECTOR)] == ["Original"]

    @pytest.mark.parametrize("kind", ["duplicate", "empty", "count", "dimension", "model"])
    def test_invalid_batch_fails_without_writing(self, db, kind):
        store, (tenant, _) = db
        docs = [article()]
        embedder = FakeEmbeddings()
        if kind == "duplicate":
            docs *= 2
        elif kind == "empty":
            docs = [article(text=" ")]
        elif kind == "count":
            embedder.embed_documents = lambda texts: []
        elif kind == "dimension":
            embedder.embed_documents = lambda texts: [[1.0] * 12 for _ in texts]
        else:
            embedder.model_name = "different-model"
        with pytest.raises(ValueError):
            ingest_articles(store, embedder, tenant, docs)
        assert store.search(tenant, VECTOR) == []

    def test_embedded_title_is_not_added_to_stored_citation_text(self, db):
        store, (tenant, _) = db
        embedder = FakeEmbeddings()
        ingest_articles(store, embedder, tenant, [article(text="Exact source substring")])
        row = store.search(tenant, VECTOR)[0]
        assert row["text"] == "Exact source substring"
        assert row["title"] == "Returns title"
        assert embedder.inputs == ["Returns title\n\nExact source substring"]

    def test_a_different_store_model_is_rejected_before_embedding(self, db):
        store, (tenant, _) = db
        wrong_store = KnowledgeStore(store.conn, "different-model")
        with pytest.raises(ValueError, match="match"):
            ingest_articles(wrong_store, FakeEmbeddings(), tenant, [article()])

    def test_day1_experiment_cannot_replace_the_real_help_center(self, db, monkeypatch):
        from caseflow import cli

        store, _ = db
        store.conn.execute(
            "INSERT INTO tenants (id, name) VALUES ('northwind', 'Test') ON CONFLICT DO NOTHING"
        )
        ingest_articles(
            store,
            FakeEmbeddings(),
            "northwind",
            [Article("returns-policy", "Real title", "real.md", "Keep the full help article")],
        )

        @contextmanager
        def same_connection(settings):
            yield store.conn

        fake = FakeEmbeddings()
        fake.embed_query = lambda text: VECTOR
        monkeypatch.setattr(cli, "bootstrap", lambda settings: {})
        monkeypatch.setattr(cli, "connect", same_connection)
        monkeypatch.setattr(cli, "FastEmbedAdapter", lambda settings: fake)
        result = cli.check_search(Settings())
        assert result["tenant_id"] == "northwind-day1-demo"
        assert store.search("northwind", VECTOR)[0]["text"] == "Keep the full help article"
        assert len(store.search("northwind-day1-demo", VECTOR)) == 3
