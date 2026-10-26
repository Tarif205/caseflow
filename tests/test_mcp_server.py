import os
from contextlib import contextmanager

import psycopg
import pytest

from support_copilot import mcp_server
from support_copilot.auth import provision_token
from support_copilot.config import Settings
from support_copilot.database import connect


def test_exact_three_read_only_schemas_have_no_authority_arguments():
    tools = mcp_server.tool_definitions()
    assert {t.name for t in tools} == {
        "search_knowledge_base",
        "get_order_status",
        "list_open_tickets",
    }
    for tool in tools:
        assert tool.inputSchema["additionalProperties"] is False
        assert not {"tenant_id", "token", "approved", "url"} & set(tool.inputSchema["properties"])
        assert tool.annotations.readOnlyHint and not tool.annotations.destructiveHint
        assert tool.outputSchema["type"] == "object"


@pytest.mark.parametrize(
    "name,args",
    [
        ("search_knowledge_base", {"query": ""}),
        ("search_knowledge_base", {"query": "   "}),
        ("search_knowledge_base", {"query": "x" * 1001}),
        ("search_knowledge_base", {"query": "policy", "top_k": True}),
        ("search_knowledge_base", {"query": "policy", "top_k": 6}),
        ("search_knowledge_base", {"query": "policy", "tenant_id": "foreign"}),
        ("get_order_status", {"order_id": "../../CT-2001"}),
        ("get_order_status", {"order_id": "NW-1044", "approved": True}),
        ("list_open_tickets", {"limit": "2"}),
        ("list_open_tickets", {"limit": 21}),
        ("list_open_tickets", {"limit": 0}),
        ("execute_refund", {}),
    ],
)
def test_bad_arguments_fail_before_any_database_or_embedding(name, args, monkeypatch):
    def forbidden(*a, **kw):
        raise AssertionError("Bad request reached database")

    monkeypatch.setattr(mcp_server, "connect", forbidden)
    with pytest.raises(mcp_server.ReadFailure) as error:
        mcp_server.MCPReads(Settings(), "x" * 43).call(name, args)
    assert error.value.code == "invalid_arguments"


def test_missing_token_fails_without_database_access(monkeypatch):
    def forbidden(*a, **kw):
        raise AssertionError("Missing auth reached database")

    monkeypatch.setattr(mcp_server, "connect", forbidden)
    with pytest.raises(mcp_server.ReadFailure) as error:
        mcp_server.MCPReads(Settings(), "").call("list_open_tickets", {})
    assert error.value.code == "forbidden"


@pytest.fixture
def reads(db, monkeypatch):
    store, (a, b) = db
    conn = store.conn
    vector = [1.0] + [0.0] * 383
    for tenant, secret, order in [(a, "A-only", "NW-1044"), (b, "B-private", "CT-2001")]:
        store.put_document(tenant, "shared", "Title", "policy.md", [secret], [vector])
        conn.execute(
            "INSERT INTO customers (tenant_id,id,name) VALUES (%s,'c1','Not exposed')", (tenant,)
        )
        conn.execute(
            """INSERT INTO orders (tenant_id,id,customer_id,status,total_cents,currency,tracking_number,placed_on)
                      VALUES (%s,%s,'c1','delivered',7500,'USD',%s,'2026-10-20')""",
            (tenant, order, secret),
        )
        conn.execute(
            """INSERT INTO tickets (tenant_id,id,customer_id,text,status)
                      VALUES (%s,'t1','c1',%s,'open'),(%s,'closed','c1','Hidden closed','closed')""",
            (tenant, secret, tenant),
        )
    provision_token(conn, a, "x" * 43, ["kb:read", "orders:read", "tickets:read"])
    provision_token(conn, b, "y" * 43, ["kb:read", "orders:read", "tickets:read"])
    provision_token(conn, a, "z" * 43, ["kb:read"])

    @contextmanager
    def borrowed(settings, *, read_only=False):
        assert read_only
        yield conn

    monkeypatch.setattr(mcp_server, "connect", borrowed)

    class Embed:
        model_name = "test-model"

        def embed_query(self, text):
            return vector

    cfg = Settings(embed_model="test-model")
    return (
        mcp_server.MCPReads(cfg, "x" * 43, Embed()),
        mcp_server.MCPReads(cfg, "y" * 43, Embed()),
        conn,
        a,
        b,
        Embed(),
    )


@pytest.mark.integration
def test_tool_results_are_exact_projected_fields_and_tenant_bound(reads):
    a, b, conn, _, _, _ = reads
    result = a.call("search_knowledge_base", {"query": "policy"})
    assert len(result["results"]) == 1 and result["results"][0]["text"] == "A-only"
    assert set(result["results"][0]) == set(mcp_server.SearchHit.model_fields)
    assert b.call("search_knowledge_base", {"query": "policy"})["results"][0]["text"] == "B-private"
    order = a.call("get_order_status", {"order_id": "NW-1044"})
    assert set(order) == set(mcp_server.OrderResult.model_fields)
    assert "tenant_id" not in order and "placed_on" not in order
    tickets = a.call("list_open_tickets", {})["tickets"]
    assert tickets == [{"id": "t1", "customer_id": "c1", "text": "A-only", "status": "open"}]
    assert b.call("list_open_tickets", {})["tickets"][0]["text"] == "B-private"


@pytest.mark.integration
def test_missing_and_foreign_records_have_identical_safe_error(reads):
    a, *_ = reads
    errors = []
    for order in ["CT-2001", "NW-9999"]:
        with pytest.raises(mcp_server.ReadFailure) as error:
            a.call("get_order_status", {"order_id": order})
        errors.append((error.value.code, str(error.value)))
    assert errors == [("not_found", "Record not found")] * 2


@pytest.mark.integration
def test_scope_and_live_revocation_are_checked_on_each_call(reads):
    a, b, conn, tenant, other, embed = reads
    limited = mcp_server.MCPReads(Settings(embed_model="test-model"), "z" * 43, embed)
    with pytest.raises(mcp_server.ReadFailure) as error:
        limited.call("list_open_tickets", {})
    assert error.value.code == "forbidden"
    assert a.call("list_open_tickets", {})["tickets"]
    conn.execute("UPDATE api_tokens SET revoked_at=now() WHERE tenant_id=%s", (tenant,))
    with pytest.raises(mcp_server.ReadFailure) as error:
        a.call("list_open_tickets", {})
    assert error.value.code == "forbidden"


@pytest.mark.integration
def test_database_transaction_read_only_cannot_write(db):
    cfg = Settings(database_url=os.environ["TEST_DATABASE_URL"])
    with connect(cfg, read_only=True) as conn:
        assert (
            conn.execute("SHOW transaction_read_only").fetchone()["transaction_read_only"] == "on"
        )
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            conn.execute("INSERT INTO tenants (id,name) VALUES ('mcp-readonly-test','No write')")
