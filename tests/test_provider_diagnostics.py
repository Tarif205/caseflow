import json

import httpx
import pytest

from support_copilot.agent_graph import GraphModel, Intake
from support_copilot.chat import HttpChatModel, InvalidModelOutput, ModelUnavailable
from support_copilot.config import Settings


def cfg():
    return Settings(
        llm_provider="openai_compatible",
        llm_model="openai/gpt-oss-20b",
        llm_base_url="https://provider.test/v1",
        llm_api_key="fake-key",
    )


def test_strict_schema_low_reasoning_and_single_bounded_retry(monkeypatch):
    requests = []
    sleeps = []
    monkeypatch.setattr("support_copilot.agent_graph.time.sleep", sleeps.append)

    def handler(request):
        body = json.loads(request.content)
        requests.append(body)
        assert body["max_tokens"] == 1200 and body["reasoning_effort"] == "low"
        spec = body["response_format"]["json_schema"]
        assert spec["strict"] and set(spec["schema"]["required"]) == set(
            spec["schema"]["properties"]
        )
        if len(requests) == 1:
            return httpx.Response(
                429,
                headers={"retry-after": "1"},
                json={"error": {"code": "rate_limit_exceeded", "message": "SECRET"}},
            )
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"finish_reason": "stop", "message": {"content": '{"intent":"escalate"}'}}
                ]
            },
        )

    model = GraphModel(cfg(), httpx.MockTransport(handler))
    assert model.complete_json([], Intake, 60).intent == "escalate"
    assert len(requests) == 2 and sleeps == [1] and model.retry_count == 1


def test_unknown_error_fields_never_escape_or_break_classification():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            400, json={"error": {"code": {"SECRET": "value"}, "message": "SECRET"}}
        )
    )
    with pytest.raises(ModelUnavailable) as error:
        HttpChatModel(cfg(), transport).complete_json([])
    assert error.value.diagnostic == {"kind": "http_error", "http_status": 400}
    assert "SECRET" not in str(error.value)


def test_json_validation_errors_are_output_failures_not_outages():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            400, json={"error": {"code": "json_validate_failed", "failed_generation": "SECRET"}}
        )
    )
    with pytest.raises(InvalidModelOutput) as error:
        HttpChatModel(cfg(), transport).complete_json([])
    assert error.value.diagnostic["code"] == "json_validate_failed"
    assert "SECRET" not in str(error.value)


def test_token_limit_is_recorded_without_partial_reasoning():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200, json={"choices": [{"finish_reason": "length", "message": {"content": "SECRET"}}]}
        )
    )
    with pytest.raises(InvalidModelOutput) as error:
        HttpChatModel(cfg(), transport).complete_json([])
    assert error.value.diagnostic == {"kind": "token_limit"}


def test_long_retry_after_is_not_slept_or_retried(monkeypatch):
    def forbidden(seconds):
        raise AssertionError("Unbounded wait")

    monkeypatch.setattr("support_copilot.agent_graph.time.sleep", forbidden)
    model = GraphModel(
        cfg(),
        httpx.MockTransport(lambda request: httpx.Response(429, headers={"retry-after": "120"})),
    )
    with pytest.raises(ModelUnavailable):
        model.complete_json([], Intake, 60)
    assert model.retry_count == 0
