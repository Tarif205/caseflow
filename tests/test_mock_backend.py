from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from caseflow import mock_api
from caseflow.auth import provision_token
from caseflow.config import Settings
from caseflow.mock_backend import MockStore


@pytest.fixture
def mock_client(db, monkeypatch):
    store, (tenant_a, tenant_b) = db
    for tenant, customer, order_id, tracking in [
        (tenant_a, "c1", "NW-1042", "NORTHWIND-ONLY"),
        (tenant_b, "c1", "CT-2001", "CONTOSO-ONLY"),
    ]:
        store.conn.execute(
            "INSERT INTO customers (tenant_id,id,name) VALUES (%s,%s,'Fictional')",
            (tenant, customer),
        )
        store.conn.execute(
            """INSERT INTO orders (tenant_id,id,customer_id,status,total_cents,currency,tracking_number,placed_on)
                            VALUES (%s,%s,%s,'shipped',1000,'USD',%s,'2026-10-20')""",
            (tenant, order_id, customer, tracking),
        )
        store.conn.execute(
            "INSERT INTO tickets (tenant_id,id,customer_id,text,status) VALUES (%s,'ticket',%s,%s,'open')",
            (tenant, customer, tracking),
        )
    provision_token(store.conn, tenant_a, "a" * 43, ["orders:read", "tickets:read", "agent:run"])
    provision_token(store.conn, tenant_b, "b" * 43, ["orders:read", "tickets:read"])
    provision_token(store.conn, tenant_a, "c" * 43, ["kb:read"])

    @contextmanager
    def connection(settings):
        yield store.conn

    monkeypatch.setattr(mock_api, "connect", connection)
    with TestClient(mock_api.create_app(Settings())) as client:
        yield client


@pytest.mark.integration
def test_order_and_ticket_endpoints_are_tenant_bound(mock_client):
    a = {"Authorization": "Bearer " + "a" * 43}
    b = {"Authorization": "Bearer " + "b" * 43}
    assert (
        mock_client.get("/orders/NW-1042", headers=a).json()["tracking_number"] == "NORTHWIND-ONLY"
    )
    foreign = mock_client.get("/orders/CT-2001", headers=a)
    absent = mock_client.get("/orders/NW-9999", headers=a)
    assert foreign.status_code == absent.status_code == 404
    assert foreign.json() == absent.json()
    assert "CONTOSO" not in mock_client.get("/tickets", headers=a).text
    assert mock_client.get("/orders/CT-2001", headers=b).json()["tracking_number"] == "CONTOSO-ONLY"


@pytest.mark.integration
def test_scopes_unknown_query_fields_and_disabled_refund(mock_client):
    read = {"Authorization": "Bearer " + "a" * 43}
    wrong = {"Authorization": "Bearer " + "c" * 43}
    assert mock_client.get("/orders/NW-1042", headers=wrong).status_code == 403
    assert mock_client.get("/tickets", headers=wrong).status_code == 403
    assert mock_client.get("/orders/NW-1042?tenant=contoso", headers=read).status_code == 422
    assert mock_client.get("/tickets?tenant_id=contoso", headers=read).status_code == 422
    assert mock_client.get("/tickets?limit=0", headers=read).status_code == 422
    assert (
        mock_client.post(
            "/refunds", headers=read, json={"approved": True, "order_id": "NW-1042"}
        ).status_code
        == 501
    )
    assert mock_client.get("/orders/NW-1042", headers=read).json()["status"] == "shipped"


def test_missing_or_malformed_token_fails_before_database(monkeypatch):
    def forbidden(*args):
        raise AssertionError("Unauthenticated request reached DB")

    monkeypatch.setattr(mock_api, "connect", forbidden)
    with TestClient(mock_api.create_app(Settings())) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/orders/NW-1042").status_code == 401
        assert (
            client.get("/orders/NW-1042", headers={"Authorization": "Bearer bad"}).status_code
            == 401
        )


@pytest.mark.integration
def test_store_filters_even_sql_like_tenant_input(db):
    store, _ = db
    assert MockStore(store.conn).get_order("' OR 1=1 --", "NW-1042") is None
    assert MockStore(store.conn).open_tickets("' OR 1=1 --") == []


@pytest.mark.integration
def test_expired_and_revoked_credentials_cannot_read_records(db, mock_client):
    from datetime import UTC, datetime, timedelta

    from caseflow.auth import hash_token

    store, (tenant, _) = db
    provision_token(
        store.conn, tenant, "d" * 43, ["orders:read"], datetime.now(UTC) - timedelta(days=1)
    )
    provision_token(store.conn, tenant, "e" * 43, ["orders:read"])
    store.conn.execute(
        "UPDATE api_tokens SET revoked_at=now() WHERE token_hash=%s", (hash_token("e" * 43),)
    )
    for token in ["d" * 43, "e" * 43]:
        assert (
            mock_client.get(
                "/orders/NW-1042", headers={"Authorization": "Bearer " + token}
            ).status_code
            == 401
        )


@pytest.mark.integration
def test_mock_seed_is_idempotent_and_preserves_changed_orders(db, monkeypatch):
    from caseflow import mock_backend
    from caseflow.config import PROJECT_ROOT

    store, _ = db
    for tenant in ["northwind", "contoso"]:
        store.conn.execute(
            "INSERT INTO tenants (id,name) VALUES (%s,%s) ON CONFLICT DO NOTHING", (tenant, tenant)
        )

    @contextmanager
    def connection(settings):
        yield store.conn

    monkeypatch.setattr(mock_backend, "connect", connection)
    path = PROJECT_ROOT / "data/mock/entities.json"
    mock_backend.seed_mock(Settings(), path)
    store.conn.execute(
        "UPDATE orders SET status='delivered' WHERE tenant_id='northwind' AND id='NW-1042'"
    )
    mock_backend.seed_mock(Settings(), path)
    assert store.conn.execute("SELECT count(*) AS n FROM orders").fetchone()["n"] == 5
    assert MockStore(store.conn).get_order("northwind", "NW-1042")["status"] == "delivered"
    assert MockStore(store.conn).get_order("contoso", "NW-1042") is None
