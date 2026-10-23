import json
from contextlib import contextmanager

import pytest
from dotenv import dotenv_values

from support_copilot import bootstrap
from support_copilot.auth import authenticate
from support_copilot.config import PROJECT_ROOT, Settings


@pytest.fixture
def operator_db(db, monkeypatch):
    store, tenants = db

    @contextmanager
    def same_connection(settings):
        yield store.conn

    monkeypatch.setattr(bootstrap, "connect", same_connection)
    return store, tenants


@pytest.mark.integration
def test_token_provisioning_preserves_env_and_returns_no_secret(operator_db, tmp_path):
    store, (tenant, _) = operator_db
    path = tmp_path / ".env"
    original = "OTHER_SETTING=keep-this-exactly\n"
    path.write_text(original)
    result = bootstrap.provision_env_token(Settings(), tenant, ["kb:read"], "TEST_API_TOKEN", path)
    token = dotenv_values(path)["TEST_API_TOKEN"]
    assert path.read_text().startswith(original)
    assert token not in json.dumps(result)
    assert authenticate(store.conn, token).tenant_id == tenant
    before = path.read_bytes()
    assert (
        bootstrap.provision_env_token(Settings(), tenant, ["kb:read"], "TEST_API_TOKEN", path)
        == result
    )
    assert path.read_bytes() == before
    with pytest.raises(ValueError, match="differs"):
        bootstrap.provision_env_token(Settings(), tenant, ["kb:write"], "TEST_API_TOKEN", path)


def test_token_provisioning_rejects_wrong_names_and_empty_placeholders(tmp_path):
    path = tmp_path / ".env"
    with pytest.raises(ValueError, match="setting name"):
        bootstrap.provision_env_token(Settings(), "northwind", ["kb:read"], "LLM_API_KEY", path)
    path.write_text("TEST_API_TOKEN=\n")
    with pytest.raises(ValueError, match="placeholder"):
        bootstrap.provision_env_token(Settings(), "northwind", ["kb:read"], "TEST_API_TOKEN", path)


@pytest.mark.integration
def test_seed_imports_empty_tenants_once_and_preserves_operator_changes(operator_db, monkeypatch):
    store, _ = operator_db
    for tenant in ("northwind", "contoso"):
        store.conn.execute("INSERT INTO tenants (id, name) VALUES (%s, %s)", (tenant, tenant))
    vector = [1.0] + [0.0] * 383

    class FakeEmbeddings:
        model_name = "test-model"
        dimension = 384

        def embed_documents(self, texts):
            return [vector for _ in texts]

    monkeypatch.setattr(bootstrap, "FastEmbedAdapter", lambda settings: FakeEmbeddings())
    result = bootstrap.seed_empty_corpus(Settings(), PROJECT_ROOT / "data")
    assert result["northwind"]["documents"] == 15
    assert result["contoso"]["documents"] == 3
    store.put_document(
        "northwind", "returns-policy", "Operator edit", "api", ["Keep the operator edit"], [vector]
    )
    again = bootstrap.seed_empty_corpus(Settings(), PROJECT_ROOT / "data")
    assert again["northwind"]["status"] == "kept_existing"
    stored = store.conn.execute(
        "SELECT title FROM documents WHERE tenant_id = 'northwind' AND id = 'returns-policy'"
    ).fetchone()
    assert stored["title"] == "Operator edit"


@pytest.mark.parametrize(
    "changes",
    [
        {"min_similarity": float("nan")},
        {"min_similarity": 2},
        {"llm_timeout": -1},
        {"llm_timeout": float("inf")},
        {"chunk_size": True},
        {"chunk_overlap": 800},
    ],
)
def test_invalid_runtime_settings_fail_early(changes):
    with pytest.raises(ValueError):
        Settings(**changes)
