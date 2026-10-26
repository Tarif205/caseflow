from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from test_approvals import ledger as ledger

from support_copilot import agent_api, durable_agent, mock_api
from support_copilot.config import Settings
from support_copilot.durable_agent import DurableAgent
from support_copilot.mock_backend import MockStore


class Model:
    def complete_json(self, messages, schema, timeout):
        return schema.model_validate(
            {"intent": "refund", "order_id": "NW-1044", "amount_cents": 7500}
            if schema.__name__ == "Intake"
            else {"action": "refund"}
        )


@pytest.fixture
def api(ledger, monkeypatch, tmp_path):
    service, actors, unused = ledger

    @contextmanager
    def borrowed(cfg):
        yield service.conn

    for module in (agent_api, durable_agent, mock_api):
        monkeypatch.setattr(module, "connect", borrowed)
    backend = TestClient(mock_api.create_app(Settings(), enable_refunds=True))

    class Tools:
        def __init__(self, actor):
            self.principal = actor

        def execute(self, name, args, timeout):
            return MockStore(service.conn).get_order(self.principal.tenant_id, args["order_id"])

    def factory(actor, token):
        def execute(run_id):
            response = backend.post(
                "/refunds", json={"run_id": run_id}, headers={"Authorization": "Bearer " + token}
            )
            assert response.status_code == 200
            return response.json()

        return DurableAgent(
            Settings(), Model(), Tools(actor), tmp_path / "api.sqlite", executor=execute
        )

    with TestClient(agent_api.create_app(Settings(), agent_factory=factory)) as client:
        yield client, backend, service, actors


def headers(letter):
    return {"Authorization": "Bearer " + letter * 43}


@pytest.mark.integration
def test_full_authenticated_http_approval_and_refund_path(api):
    client, backend, service, actors = api
    response = client.post("/runs", json={"ticket_id": "t1"}, headers=headers("w"))
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "needs_approval" and not result["refund_executed"]
    run_id = result["run_id"]
    assert client.get(f"/runs/{run_id}", headers=headers("w")).json()["status"] == "needs_approval"
    assert client.post(f"/runs/{run_id}/resume", headers=headers("w")).status_code == 403
    assert (
        backend.post("/refunds", json={"run_id": run_id}, headers=headers("w")).status_code == 403
    )
    pending = client.get("/approvals", headers=headers("a")).json()["pending"]
    assert any(row["run_id"] == run_id for row in pending)
    assert (
        client.post(
            f"/approvals/{run_id}/decision", json={"approved": True}, headers=headers("a")
        ).status_code
        == 200
    )
    completed = client.post(f"/runs/{run_id}/resume", headers=headers("w")).json()
    assert completed["status"] == "refunded" and completed["refund_executed"]
    assert (
        client.post(f"/runs/{run_id}/resume", headers=headers("w")).json()["status"] == "refunded"
    )
    assert (
        service.conn.execute(
            "SELECT count(*) n FROM refunds WHERE tenant_id=%s", (actors["worker"].tenant_id,)
        ).fetchone()["n"]
        == 1
    )


@pytest.mark.integration
def test_cross_tenant_scopes_and_forged_approval_payloads(api):
    client, backend, _, _ = api
    started = client.post("/runs", json={"ticket_id": "t1"}, headers=headers("w")).json()
    run_id = started["run_id"]
    assert client.get(f"/runs/{run_id}", headers=headers("f")).status_code == 403
    assert (
        client.post(
            f"/approvals/{run_id}/decision", json={"approved": True}, headers=headers("f")
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/approvals/{run_id}/decision", json={"approved": True}, headers=headers("w")
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/runs/{run_id}/resume", json={"approved": True}, headers=headers("w")
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/runs", json={"ticket_id": "t1", "tenant_id": "other"}, headers=headers("w")
        ).status_code
        == 422
    )
    assert (
        backend.post(
            "/refunds", json={"run_id": run_id, "approved": True}, headers=headers("w")
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/approvals/{run_id}/decision", json={"approved": "true"}, headers=headers("a")
        ).status_code
        == 422
    )


def test_missing_malformed_auth_does_not_reach_database(monkeypatch):
    def forbidden(*args):
        raise AssertionError("Unauthenticated database access")

    monkeypatch.setattr(agent_api, "connect", forbidden)
    with TestClient(agent_api.create_app(Settings())) as client:
        assert client.get("/approvals").status_code == 401
        assert client.get("/approvals", headers={"Authorization": "Bearer bad"}).status_code == 401
        assert client.post("/runs", content=b"x" * 4097).status_code == 413
