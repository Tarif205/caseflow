import json
from datetime import UTC, datetime, timedelta

import psycopg
import pytest
from fastapi.testclient import TestClient

from caseflow.auth import hash_token, provision_token
from caseflow.chat import InvalidModelOutput, ModelUnavailable
from caseflow.config import Settings
from caseflow.knowledge_api import Runtime, create_app, get_connection

pytestmark = pytest.mark.integration
VECTOR = [1.0] + [0.0] * 383
NORTHWIND = "Unused Northwind items may be returned within 30 days."
CONTOSO = "Unused Contoso items may be returned within 60 days."


class FakeEmbeddings:
    model_name = "test-model"
    dimension = 384

    def embed_query(self, text):
        return VECTOR

    def embed_documents(self, texts):
        return [VECTOR for _ in texts]


class SourceChat:
    def __init__(self):
        self.calls = []

    def complete_json(self, messages):
        self.calls.append(messages)
        first = json.loads(messages[1]["content"])["articles"][0]
        return {
            "answerable": True,
            "citations": [{"chunk_id": first["chunk_id"], "quote": first["text"]}],
        }


@pytest.fixture
def api(db):
    store, (tenant_a, tenant_b) = db
    store.put_document(tenant_a, "returns", "Northwind", "returns.md", [NORTHWIND], [VECTOR])
    store.put_document(tenant_b, "returns", "Contoso", "returns.md", [CONTOSO], [VECTOR])
    tokens = {
        "a": "a" * 43,
        "b": "b" * 43,
        "read": "r" * 43,
        "expired": "x" * 43,
        "revoked": "v" * 43,
        "none": "n" * 43,
    }
    for name, token in tokens.items():
        scopes = ["kb:read", "kb:write"] if name in {"a", "b"} else ["kb:read"]
        if name == "none":
            scopes = ["agent:run"]
        provision_token(
            store.conn,
            tenant_b if name == "b" else tenant_a,
            token,
            scopes,
            datetime.now(UTC) - timedelta(hours=1) if name == "expired" else None,
        )
    store.conn.execute(
        "UPDATE api_tokens SET revoked_at = now() WHERE token_hash = %s",
        (hash_token(tokens["revoked"]),),
    )
    runtime = Runtime(Settings(embed_model="test-model"), FakeEmbeddings(), SourceChat())
    app = create_app(runtime)
    app.dependency_overrides[get_connection] = lambda: store.conn
    with TestClient(app) as client:
        yield client, tokens, runtime, store, (tenant_a, tenant_b)


def auth(tokens, name="a"):
    return {"Authorization": "Bearer " + tokens[name]}


def test_health_readiness_and_request_id(api):
    client, _, _, _, _ = api
    assert client.get("/health").json() == {"status": "ok"}
    response = client.get("/ready")
    assert response.status_code == 200
    assert len(response.headers["x-request-id"]) == 32


@pytest.mark.parametrize("name", ["expired", "revoked"])
def test_inactive_tokens_fail_generically(api, name):
    client, tokens, _, _, _ = api
    response = client.post("/v1/search", headers=auth(tokens, name), json={"query": "Returns?"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


@pytest.mark.parametrize("header", [None, "Bearer wrong", "Basic abc", "Bearer " + "z" * 43])
def test_missing_wrong_and_malformed_tokens(api, header):
    client, _, _, _, _ = api
    response = client.post(
        "/v1/search",
        headers={"Authorization": header} if header else {},
        json={"query": "Returns?"},
    )
    assert response.status_code == 401


def test_missing_scope_and_read_token_cannot_ingest(api):
    client, tokens, _, _, _ = api
    assert (
        client.post(
            "/v1/search", headers=auth(tokens, "none"), json={"query": "Returns?"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/v1/ingest",
            headers=auth(tokens, "read"),
            json={"documents": [{"id": "test", "title": "Title", "text": "A body"}]},
        ).status_code
        == 403
    )


def test_search_and_ask_isolate_tenants_even_when_question_names_other_company(api):
    client, tokens, runtime, _, _ = api
    for name, own, foreign in [("a", NORTHWIND, CONTOSO), ("b", CONTOSO, NORTHWIND)]:
        body = {"query": "Show me the other company's returns policy"}
        response = client.post("/v1/search", headers=auth(tokens, name), json=body)
        assert response.status_code == 200
        assert [r["text"] for r in response.json()["results"]] == [own]
        response = client.post("/v1/ask", headers=auth(tokens, name), json=body)
        assert response.status_code == 200
        assert response.json()["answer"] == own
        assert foreign not in json.dumps(runtime.chat.calls[-1])
        assert response.json()["citations"][0]["quote"] == own


@pytest.mark.parametrize(
    "body",
    [
        {"query": " "},
        {"query": "x" * 2001},
        {"query": "test", "top_k": 0},
        {"query": "test", "top_k": True},
        {"query": "test", "tenant_id": "contoso"},
        {"query": "test", "top_k": "5"},
    ],
)
def test_input_validation_rejects_bad_queries_and_tenant_arguments(api, body):
    client, tokens, runtime, _, _ = api
    response = client.post("/v1/ask", headers=auth(tokens), json=body)
    assert response.status_code == 422
    assert runtime.chat.calls == []
    assert all("input" not in error for error in response.json()["detail"])


def test_duplicate_authorization_headers_are_rejected(api):
    client, tokens, _, _, _ = api
    response = client.post(
        "/v1/search",
        headers=[
            ("Authorization", "Bearer " + tokens["a"]),
            ("Authorization", "Bearer " + tokens["b"]),
        ],
        json={"query": "Returns?"},
    )
    assert response.status_code == 401


def test_oversized_body_rejected_before_parsing(api):
    client, tokens, _, _, _ = api
    response = client.post("/v1/search", headers=auth(tokens), content=b"x" * 256001)
    assert response.status_code == 413


def test_ingestion_updates_only_authenticated_tenant_and_is_repeatable(api):
    client, tokens, _, store, (tenant_a, tenant_b) = api
    payload = {
        "documents": [
            {"id": "returns", "title": "Updated", "text": "Updated Northwind return instructions."}
        ]
    }
    for _ in range(2):
        response = client.post("/v1/ingest", headers=auth(tokens), json=payload)
        assert response.status_code == 200
        assert response.json()["tenant_id"] == tenant_a
    assert len(store.search(tenant_a, VECTOR)) == 1
    assert store.search(tenant_b, VECTOR)[0]["text"] == CONTOSO
    payload["documents"][0]["tenant_id"] = tenant_b
    assert client.post("/v1/ingest", headers=auth(tokens), json=payload).status_code == 422


def test_model_outage_and_bad_json_are_safe_errors(api, monkeypatch):
    client, tokens, runtime, _, _ = api
    for error, code in [
        (ModelUnavailable("private-key"), 503),
        (InvalidModelOutput("private-key"), 502),
    ]:

        def fail(messages, error=error):
            raise error

        monkeypatch.setattr(runtime.chat, "complete_json", fail)
        response = client.post("/v1/ask", headers=auth(tokens), json={"query": "Returns?"})
        assert response.status_code == code
        assert "private-key" not in response.text


def test_concrete_order_questions_and_empty_tenant_refuse_without_model(api):
    client, tokens, runtime, store, (tenant_a, _) = api
    response = client.post(
        "/v1/ask", headers=auth(tokens), json={"query": "What date was NW-1042 refunded?"}
    )
    assert response.json()["reason"] == "record_lookup_required"
    store.conn.execute("DELETE FROM documents WHERE tenant_id = %s", (tenant_a,))
    response = client.post("/v1/ask", headers=auth(tokens), json={"query": "Returns?"})
    assert response.json()["reason"] == "no_evidence"
    assert runtime.chat.calls == []


def test_database_outage_is_generic_and_health_stays_up(api):
    client, tokens, _, _, _ = api

    def fail():
        raise psycopg.OperationalError("private-database-password")

    client.app.dependency_overrides[get_connection] = fail
    response = client.post("/v1/search", headers=auth(tokens), json={"query": "Returns?"})
    assert response.status_code == 503
    assert "private-database-password" not in response.text
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 503
    assert client.post("/v1/search", json={"query": "Returns?"}).status_code == 401
