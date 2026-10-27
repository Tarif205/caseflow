import secrets
from contextlib import contextmanager

import pytest

from caseflow import mcp_credentials as cloud
from caseflow.auth import authenticate, hash_token
from caseflow.config import Settings


@pytest.fixture
def provisioning(db, monkeypatch):
    store, _ = db
    conn = store.conn
    for tenant in ("northwind", "contoso"):
        conn.execute(
            "INSERT INTO tenants (id,name) VALUES (%s,'Fixture') ON CONFLICT DO NOTHING", (tenant,)
        )

    @contextmanager
    def borrowed(settings):
        with conn.transaction():
            yield conn

    monkeypatch.setattr(cloud, "connect", borrowed)
    credentials = {tenant: secrets.token_urlsafe(32) for tenant in ("northwind", "contoso")}
    return conn, credentials


def test_read_only_hash_provisioning_is_idempotent_and_tenant_bound(provisioning):
    conn, credentials = provisioning
    cloud.provision(Settings(), credentials)
    cloud.provision(Settings(), credentials)
    for tenant, token in credentials.items():
        actor = authenticate(conn, token)
        assert actor.tenant_id == tenant and actor.scopes == cloud.SCOPES
        row = conn.execute(
            "SELECT token_hash FROM api_tokens WHERE token_hash=%s", (hash_token(token),)
        ).fetchall()
        assert len(row) == 1 and row[0]["token_hash"] != token


def test_existing_scope_mismatch_is_not_overwritten(provisioning):
    conn, credentials = provisioning
    cloud.provision(Settings(), credentials)
    token = credentials["northwind"]
    conn.execute(
        "UPDATE api_tokens SET scopes=ARRAY['kb:read'] WHERE token_hash=%s", (hash_token(token),)
    )
    with pytest.raises(ValueError):
        cloud.provision(Settings(), credentials)
    assert authenticate(conn, token).scopes == frozenset({"kb:read"})


@pytest.mark.parametrize("field", ["revoked_at", "expires_at"])
def test_inactive_credential_is_not_revived(provisioning, field):
    conn, credentials = provisioning
    cloud.provision(Settings(), credentials)
    token = credentials["northwind"]
    assert field in {"revoked_at", "expires_at"}
    conn.execute(
        f"UPDATE api_tokens SET {field}=now()-interval '1 day' WHERE token_hash=%s",
        (hash_token(token),),
    )
    with pytest.raises(ValueError):
        cloud.provision(Settings(), credentials)
    assert authenticate(conn, token) is None


def test_second_invalid_credential_rolls_back_first_insert(provisioning):
    conn, credentials = provisioning
    with pytest.raises(ValueError):
        cloud.provision(Settings(), {**credentials, "contoso": "invalid"})
    assert (
        conn.execute(
            "SELECT 1 FROM api_tokens WHERE token_hash=%s", (hash_token(credentials["northwind"]),)
        ).fetchone()
        is None
    )
