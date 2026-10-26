import json
from dataclasses import replace

import httpx
import pytest

from support_copilot.agent_tools import BoundTools
from support_copilot.auth import Principal
from support_copilot.chat import InvalidModelOutput, ModelUnavailable
from support_copilot.config import Settings
from support_copilot.tool_chat import HttpToolModel, ModelTurn, ToolCall, parse_turn


@pytest.mark.parametrize("arguments", [{"order_id": "NW-1042"}, '{"order_id":"NW-1042"}'])
def test_parse_both_provider_argument_shapes(arguments):
    turn = parse_turn(
        {
            "content": None,
            "tool_calls": [{"id": "x", "function": {"name": "get_order", "arguments": arguments}}],
        }
    )
    assert turn.calls[0].arguments == {"order_id": "NW-1042"}


@pytest.mark.parametrize(
    "raw",
    [
        {"tool_calls": "bad"},
        {"tool_calls": [{"function": {"name": "x", "arguments": "[1]"}}]},
        {"content": 42},
    ],
)
def test_bad_native_messages_rejected(raw):
    with pytest.raises(InvalidModelOutput):
        parse_turn(raw)


@pytest.mark.parametrize("provider", ["ollama", "openai_compatible"])
def test_wire_messages_are_provider_specific_without_mutating_history(provider):
    messages = [
        ModelTurn("", (ToolCall("c1", "get_order", {"order_id": "NW-1042"}),)).message(),
        {"role": "tool", "name": "get_order", "tool_call_id": "c1", "content": "{}"},
    ]
    original = json.dumps(messages)

    def respond(request):
        body = json.loads(request.content)
        wire = body["messages"]
        if provider == "ollama":
            assert isinstance(wire[0]["tool_calls"][0]["function"]["arguments"], dict)
            assert wire[1]["tool_name"] == "get_order" and "tool_call_id" not in wire[1]
            return httpx.Response(200, json={"message": {"content": "{}"}})
        assert wire[1]["tool_call_id"] == "c1" and "name" not in wire[1]
        assert request.headers["Authorization"] == "Bearer secret-test-key"
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    cfg = replace(
        Settings(),
        llm_provider=provider,
        llm_base_url="https://provider.example",
        llm_api_key="secret-test-key",
    )
    HttpToolModel(cfg, httpx.MockTransport(respond)).complete(messages, [], 10)
    assert json.dumps(messages) == original


def test_provider_failure_does_not_include_secret_response():
    cfg = replace(Settings(), llm_base_url="https://provider.example")
    model = HttpToolModel(cfg, httpx.MockTransport(lambda r: httpx.Response(503, text="SECRET")))
    with pytest.raises(ModelUnavailable) as exc:
        model.complete([], [], 10)
    assert "SECRET" not in str(exc.value)


def test_bound_tools_credentials_not_in_repr_and_tenant_not_model_argument():
    principal = Principal("northwind", frozenset({"kb:read"}), "hash")
    tools = BoundTools(
        principal, "https://kb.example", "http://127.0.0.1:8004", "SECRET-KB", "SECRET-BACKEND"
    )
    assert "SECRET" not in repr(tools)
    with pytest.raises(ValueError):
        tools.execute("search_kb", {"query": "returns", "tenant": "contoso"}, 10)
