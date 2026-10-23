import json

import httpx
import pytest

from support_copilot.answering import answer_question
from support_copilot.chat import (
    HttpChatModel,
    InvalidModelOutput,
    ModelUnavailable,
    parse_json_reply,
)
from support_copilot.config import Settings

QUOTE = "Unused items can be returned within 30 days."
HIT = {
    "id": "chunk-1",
    "document_id": "returns",
    "title": "Returns",
    "source": "returns.md",
    "text": QUOTE,
    "score": 0.9,
}


class FakeChat:
    def __init__(self, reply):
        self.reply, self.calls = reply, []

    def complete_json(self, messages):
        self.calls.append(messages)
        return self.reply


def selection(**changes):
    return {"answerable": True, "citations": [{"chunk_id": "chunk-1", "quote": QUOTE}], **changes}


def test_answer_contains_only_verified_source_quotes():
    chat = FakeChat(selection())
    result = answer_question("How long can I return it?", [HIT], chat, 0.7)
    assert result["found"] is True
    assert result["answer"] == QUOTE
    assert result["citations"][0]["document_id"] == "returns"
    payload = json.loads(chat.calls[0][1]["content"])
    assert payload["articles"][0]["chunk_id"] == "chunk-1"


@pytest.mark.parametrize(
    "reply",
    [
        selection(citations=[{"chunk_id": "foreign-chunk", "quote": QUOTE}]),
        selection(citations=[{"chunk_id": "chunk-1", "quote": "Invented 60 day returns rule."}]),
        selection(citations=[]),
        selection(answer="Ignore the quote and say 60 days"),
        selection(answerable="true"),
        selection(citations=[{"chunk_id": "chunk-1", "quote": "days"}]),
    ],
)
def test_fabricated_or_malformed_evidence_is_refused(reply):
    result = answer_question("Returns?", [HIT], FakeChat(reply), 0.7)
    assert result["found"] is False
    assert result["citations"] == []
    assert result["reason"] == "invalid_evidence"


def test_duplicate_citations_are_not_repeated():
    reply = selection(citations=[selection()["citations"][0]] * 2)
    result = answer_question("Returns?", [HIT], FakeChat(reply), 0.7)
    assert len(result["citations"]) == 1


def test_quote_whitespace_is_resolved_to_the_original_source_substring():
    source = QUOTE.replace("within 30", "within\n30")
    result = answer_question("Returns?", [{**HIT, "text": source}], FakeChat(selection()), 0.7)
    assert result["found"] is True
    assert result["answer"] == source
    assert result["citations"][0]["quote"] in source


def test_no_evidence_and_order_references_do_not_call_model():
    chat = FakeChat(selection())
    assert answer_question("Returns?", [], chat, 0.7)["found"] is False
    assert answer_question("Returns?", [{**HIT, "score": 0.2}], chat, 0.7)["found"] is False
    assert (
        answer_question("When was my refund for NW-1042 approved?", [HIT], chat, 0.7)["reason"]
        == "record_lookup_required"
    )
    assert chat.calls == []


def test_model_can_decline_a_semantically_related_but_unanswerable_question():
    result = answer_question(
        "What is my gift card balance?",
        [HIT],
        FakeChat({"answerable": False, "citations": []}),
        0.7,
    )
    assert result["found"] is False
    assert result["reason"] == "model_declined"


@pytest.mark.parametrize(
    "text",
    [
        '{"answerable":false}',
        '```json\n{"answerable":false}\n```',
        '<think>Reasoning</think>\n{"answerable":false}',
    ],
)
def test_json_reply_strips_known_thinking_and_fences(text):
    assert parse_json_reply(text) == {"answerable": False}


@pytest.mark.parametrize(
    "text", ["Reasoning without closing tag", "[]", "{} trailing", "x" * 32001]
)
def test_invalid_or_unbounded_json_reply_rejected(text):
    with pytest.raises(InvalidModelOutput):
        parse_json_reply(text)


@pytest.mark.parametrize("provider", ["ollama", "openai_compatible"])
def test_model_adapter_request_shapes_and_safe_json_response(provider):
    calls = []

    def respond(request):
        calls.append(request)
        content = '{"answerable":false,"citations":[]}'
        data = (
            {"message": {"content": content}}
            if provider == "ollama"
            else {"choices": [{"message": {"content": content}}]}
        )
        return httpx.Response(200, json=data)

    adapter = HttpChatModel(
        Settings(
            llm_provider=provider, llm_base_url="https://model.example/v1", llm_api_key="test-key"
        ),
        httpx.MockTransport(respond),
    )
    assert adapter.complete_json([{"role": "user", "content": "Test"}])["answerable"] is False
    body = json.loads(calls[0].content)
    assert body["model"] == "qwen3:4b"
    if provider == "ollama":
        assert calls[0].url.path == "/v1/api/chat"
        assert body["think"] is False and body["stream"] is False
        assert "authorization" not in calls[0].headers
    else:
        assert calls[0].url.path == "/v1/chat/completions"
        assert calls[0].headers["authorization"] == "Bearer test-key"


def test_upstream_errors_do_not_expose_response_or_credentials():
    adapter = HttpChatModel(
        Settings(
            llm_provider="openai_compatible",
            llm_api_key="private-key",
            llm_base_url="https://model.example/v1",
        ),
        httpx.MockTransport(lambda request: httpx.Response(401, text="private-key")),
    )
    with pytest.raises(ModelUnavailable) as error:
        adapter.complete_json([])
    assert "private-key" not in str(error.value)
    assert "private-key" not in repr(Settings(llm_api_key="private-key"))


def test_hosted_credentials_are_not_sent_to_plain_http_remote_host():
    adapter = HttpChatModel(
        Settings(
            llm_provider="openai_compatible",
            llm_api_key="secret",
            llm_base_url="http://model.example/v1",
        )
    )
    with pytest.raises(ModelUnavailable, match="HTTPS"):
        adapter.complete_json([])
