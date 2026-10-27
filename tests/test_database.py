"""Real Postgres tests. Each test rolls back all of its own data."""

from uuid import uuid4

import numpy as np
import psycopg
import pytest

from caseflow.database import EmbeddingModelMismatch, KnowledgeStore

pytestmark = pytest.mark.integration
MODEL = "test-model"
FIRST = [1.0] + [0.0] * 383
SECOND = [0.0, 1.0] + [0.0] * 382


def put(store, tenant, doc_id, vector=FIRST, text="Example article"):
    store.put_document(tenant, doc_id, doc_id, "test-source", [text], [vector])


def test_nearest_neighbor_ordering(db):
    store, (tenant, _) = db
    put(store, tenant, "returns", FIRST)
    put(store, tenant, "shipping", SECOND)
    results = store.search(tenant, FIRST, top_k=2)
    assert [r["document_id"] for r in results] == ["returns", "shipping"]
    assert results[0]["score"] == pytest.approx(1.0)
    assert results[1]["score"] == pytest.approx(0.0)


def test_search_isolates_same_document_id_in_two_tenants(db):
    store, (tenant_a, tenant_b) = db
    put(store, tenant_a, "returns", SECOND, "Northwind public policy")
    put(store, tenant_b, "returns", FIRST, "Contoso private policy")
    assert [r["text"] for r in store.search(tenant_a, FIRST)] == ["Northwind public policy"]
    assert [r["text"] for r in store.search(tenant_b, SECOND)] == ["Contoso private policy"]


def test_reingesting_one_tenant_does_not_overwrite_another(db):
    store, (tenant_a, tenant_b) = db
    put(store, tenant_a, "shared", FIRST, "Original")
    put(store, tenant_b, "shared", FIRST, "Other tenant")
    put(store, tenant_a, "shared", FIRST, "Updated")
    assert [r["text"] for r in store.search(tenant_a, FIRST)] == ["Updated"]
    assert [r["text"] for r in store.search(tenant_b, FIRST)] == ["Other tenant"]


def test_unknown_tenant_and_sql_injection_return_no_rows(db):
    store, (tenant, _) = db
    put(store, tenant, "returns")
    assert store.search("missing", FIRST) == []
    assert store.search("' OR 1=1 --", FIRST) == []


def test_foreign_tenant_document_reference_fails_at_database_level(db):
    store, (tenant_a, tenant_b) = db
    put(store, tenant_a, "foreign")
    with pytest.raises(psycopg.errors.ForeignKeyViolation), store.conn.transaction():
        store.conn.execute(
            """INSERT INTO chunks
               (tenant_id, id, document_id, position, text, embedding, embed_model)
               VALUES (%s, %s, %s, 0, 'invalid', %s, %s)""",
            (tenant_b, uuid4(), "foreign", np.asarray(FIRST), MODEL),
        )


def test_invalid_replacement_preserves_existing_document(db):
    store, (tenant, _) = db
    put(store, tenant, "returns", text="Keep this")
    with pytest.raises(ValueError):
        store.put_document(tenant, "returns", "Bad", "test", ["Replacement"], [[1.0]])
    assert store.search(tenant, FIRST)[0]["text"] == "Keep this"


def test_reingest_is_idempotent_and_removes_obsolete_chunks(db):
    store, (tenant, _) = db
    store.put_document(tenant, "returns", "Title", "test", ["one", "two"], [FIRST, SECOND])
    put(store, tenant, "returns", text="Only one now")
    put(store, tenant, "returns", text="Only one now")
    assert len(store.search(tenant, FIRST)) == 1


def test_model_mismatch_is_detected_only_within_current_tenant(db):
    store, (tenant_a, tenant_b) = db
    put(store, tenant_a, "returns")
    changed = KnowledgeStore(store.conn, "different-model")
    put(changed, tenant_b, "shipping")
    assert len(store.search(tenant_a, FIRST)) == 1
    with pytest.raises(EmbeddingModelMismatch):
        store.search(tenant_b, FIRST)


@pytest.mark.parametrize("top_k", [0, -1, 21, True, 1.5])
def test_invalid_top_k_rejected(db, top_k):
    store, (tenant, _) = db
    with pytest.raises(ValueError):
        store.search(tenant, FIRST, top_k)


def test_postgres_rejects_wrong_vector_dimensions(db):
    store, (tenant, _) = db
    put(store, tenant, "returns")
    with pytest.raises(psycopg.Error), store.conn.transaction():
        store.conn.execute(
            "UPDATE chunks SET embedding = %s WHERE tenant_id = %s",
            (np.ones(12), tenant),
        )
