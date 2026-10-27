import json

import httpx
import pytest
from pydantic import ValidationError

from caseflow.agent_tools import RecordNotFound, ToolFailure
from caseflow.auth import Principal
from caseflow.mcp_client import MCPTools
from caseflow.mcp_server import tool_definitions

TOKEN = "x" * 43
ACTOR = Principal("tenant-a", frozenset({"agent:run", "kb:read", "orders:read"}), "worker")
ORDER = {
    "id": "NW-1044",
    "customer_id": "c1",
    "status": "delivered",
    "total_cents": 7500,
    "currency": "USD",
    "tracking_number": None,
}


def wire(*, definitions=None, value=None, error=None, status=200):
    seen = []

    def handle(request):
        seen.append(request)
        assert request.headers["authorization"] == "Bearer " + TOKEN
        assert request.url == "http://127.0.0.1:8003/mcp"
        if status != 200:
            return httpx.Response(status, json={"error": "secret upstream detail"})
        message = json.loads(request.content)
        method = message["method"]
        if "id" not in message:
            return httpx.Response(202)
        if method == "initialize":
            result = {
                "protocolVersion": "2025-11-25",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "caseflow-readonly", "version": "0.1.0"},
            }
        elif method == "tools/list":
            result = {
                "tools": definitions
                if definitions is not None
                else [t.model_dump(mode="json", exclude_none=True) for t in tool_definitions()]
            }
        elif method == "tools/call":
            result = {
                "content": [{"type": "text", "text": json.dumps(error or value or ORDER)}],
                "isError": error is not None,
            }
            if error is None:
                result["structuredContent"] = value if value is not None else ORDER
        else:
            pytest.fail("Unexpected MCP RPC")
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": message["id"], "result": result})

    return httpx.MockTransport(handle), seen


def test_sdk_adapter_discovers_calls_and_projects_both_reads():
    transport, seen = wire()
    tools = MCPTools(ACTOR, "http://127.0.0.1:8003/mcp", TOKEN, transport)
    assert tools.execute("get_order", {"order_id": "NW-1044"}, 5) == ORDER
    call = json.loads(seen[-1].content)
    assert call["method"] == "tools/call"
    assert call["params"]["name"] == "get_order_status"
    assert call["params"]["arguments"] == {"order_id": "NW-1044"}
    transport, seen = wire(value={"results": []})
    tools.transport = transport
    assert tools.execute("search_kb", {"query": " returns "}, 5) == {"results": []}
    assert json.loads(seen[-1].content)["params"]["arguments"] == {"query": "returns", "top_k": 3}
    assert TOKEN not in repr(tools)


def test_adapter_rejects_model_identity_write_and_scope_before_io():
    transport, seen = wire()
    tools = MCPTools(ACTOR, "http://127.0.0.1:8003/mcp", TOKEN, transport)
    with pytest.raises(ValidationError):
        tools.execute("get_order", {"order_id": "NW-1044", "tenant_id": "tenant-b"}, 5)
    with pytest.raises(ToolFailure):
        tools.execute("refund", {"approved": True}, 5)
    tools.principal = Principal("tenant-a", frozenset({"agent:run"}), "worker")
    with pytest.raises(ToolFailure):
        tools.execute("search_kb", {"query": "returns"}, 5)
    assert not seen


@pytest.mark.parametrize("mutation", ["extra_tool", "duplicate_tool", "schema", "write_hint"])
def test_registry_changes_fail_before_call(mutation):
    definitions = [t.model_dump(mode="json", exclude_none=True) for t in tool_definitions()]
    if mutation == "extra_tool":
        definitions.append({**definitions[0], "name": "execute_refund"})
    elif mutation == "duplicate_tool":
        definitions.append(definitions[0])
    elif mutation == "schema":
        definitions[0]["inputSchema"]["properties"]["tenant_id"] = {"type": "string"}
    else:
        definitions[0]["annotations"]["destructiveHint"] = True
    transport, seen = wire(definitions=definitions)
    with pytest.raises(ToolFailure):
        MCPTools(ACTOR, "http://127.0.0.1:8003/mcp", TOKEN, transport).execute(
            "get_order", {"order_id": "NW-1044"}, 5
        )
    assert not any(json.loads(r.content)["method"] == "tools/call" for r in seen)


def test_foreign_not_found_is_generic_and_not_confused_with_auth_failure():
    transport, _ = wire(error={"code": "not_found", "message": "hostile private text"})
    with pytest.raises(RecordNotFound, match="^Record not found$"):
        MCPTools(ACTOR, "http://127.0.0.1:8003/mcp", TOKEN, transport).execute(
            "get_order", {"order_id": "CT-2001"}, 5
        )
    transport, _ = wire(status=401)
    with pytest.raises(ToolFailure, match="^MCP read unavailable$") as caught:
        MCPTools(ACTOR, "http://127.0.0.1:8003/mcp", TOKEN, transport).execute(
            "get_order", {"order_id": "NW-1044"}, 5
        )
    assert not isinstance(caught.value, RecordNotFound)


@pytest.mark.parametrize(
    "value", [{**ORDER, "tenant_id": "tenant-b"}, {**ORDER, "total_cents": True}]
)
def test_strict_output_contract_rejects_extra_identity_and_coercion(value):
    transport, _ = wire(value=value)
    with pytest.raises(ToolFailure):
        MCPTools(ACTOR, "http://127.0.0.1:8003/mcp", TOKEN, transport).execute(
            "get_order", {"order_id": "NW-1044"}, 5
        )


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_deadline_rejected_before_io(timeout):
    transport, seen = wire()
    with pytest.raises(ToolFailure):
        MCPTools(ACTOR, "http://127.0.0.1:8003/mcp", TOKEN, transport).execute(
            "get_order", {"order_id": "NW-1044"}, timeout
        )
    assert not seen


def test_unbounded_body_and_plaintext_remote_are_rejected():
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json={"junk": "x" * 128_001}))
    with pytest.raises(ToolFailure):
        MCPTools(ACTOR, "http://127.0.0.1:8003/mcp", TOKEN, transport).execute(
            "get_order", {"order_id": "NW-1044"}, 5
        )
    with pytest.raises(ValueError):
        MCPTools(ACTOR, "http://evil.example/mcp", TOKEN)
