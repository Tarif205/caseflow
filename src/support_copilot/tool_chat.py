"""Native tool-call adapters; normalize wire differences without executing tools."""

import copy
import json
from dataclasses import dataclass
from urllib.parse import urlparse
from uuid import uuid4

import httpx

from support_copilot.chat import InvalidModelOutput, ModelUnavailable
from support_copilot.config import Settings


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass(frozen=True)
class ModelTurn:
    content: str
    calls: tuple[ToolCall, ...] = ()

    def message(self) -> dict:
        result = {"role": "assistant", "content": self.content}
        if self.calls:
            result["tool_calls"] = [
                {
                    "id": c.id,
                    "type": "function",
                    "function": {"name": c.name, "arguments": json.dumps(c.arguments)},
                }
                for c in self.calls
            ]
        return result


def parse_turn(raw: dict) -> ModelTurn:
    if not isinstance(raw, dict) or not isinstance(raw.get("content", ""), (str, type(None))):
        raise InvalidModelOutput("Invalid model message")
    content = raw.get("content") or ""
    calls = raw.get("tool_calls") or []
    if not isinstance(calls, list) or len(calls) > 4 or len(content) > 16000:
        raise InvalidModelOutput("Model response exceeded limits")
    parsed = []
    try:
        for call in calls:
            fn = call["function"]
            args = fn["arguments"]
            if isinstance(args, str):
                if len(args) > 4000:
                    raise ValueError
                args = json.loads(args)
            name = fn["name"]
            call_id = call.get("id") or "call_" + uuid4().hex
            if (
                not isinstance(args, dict)
                or not isinstance(name, str)
                or not 1 <= len(name) <= 80
                or not isinstance(call_id, str)
                or not 1 <= len(call_id) <= 120
            ):
                raise ValueError
            parsed.append(ToolCall(call_id, name, args))
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidModelOutput("Invalid tool request") from exc
    if len({c.id for c in parsed}) != len(parsed):
        raise InvalidModelOutput("Duplicate tool-call ids")
    return ModelTurn(content, tuple(parsed))


class HttpToolModel:
    def __init__(self, settings: Settings, transport=None):
        self.settings = settings
        self.transport = transport

    def complete(self, messages: list[dict], tools: list[dict], timeout: float) -> ModelTurn:
        cfg = self.settings
        parsed = urlparse(cfg.llm_base_url)
        if parsed.scheme not in {"https", "http"} or not parsed.hostname:
            raise ModelUnavailable("Invalid tool-model URL")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ModelUnavailable("Invalid tool-model URL")
        if timeout <= 0:
            raise ModelUnavailable("Tool-model budget exhausted")
        wire = copy.deepcopy(messages)
        headers = {"Content-Type": "application/json"}
        body = {"model": cfg.llm_model, "messages": wire, "tools": tools, "stream": False}
        if cfg.llm_provider == "ollama":
            for message in wire:
                for call in message.get("tool_calls", []):
                    call["function"]["arguments"] = json.loads(call["function"]["arguments"])
                if message["role"] == "tool":
                    message["tool_name"] = message.pop("name")
                    message.pop("tool_call_id", None)
            url = cfg.llm_base_url + "/api/chat"
            body.update(
                think=False,
                keep_alive="0",
                options={"temperature": 0, "num_predict": 700, "num_ctx": 4096},
            )
        elif cfg.llm_provider == "openai_compatible":
            for message in wire:
                if message["role"] == "tool":
                    message.pop("name", None)
            if not cfg.llm_api_key or (
                parsed.scheme != "https"
                and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            ):
                raise ModelUnavailable("Hosted tool-model credentials require HTTPS")
            url = cfg.llm_base_url + "/chat/completions"
            headers["Authorization"] = "Bearer " + cfg.llm_api_key
            body.update(
                temperature=0, max_tokens=700, tool_choice="auto", parallel_tool_calls=False
            )
        else:
            raise ModelUnavailable("Unsupported tool-model provider")
        try:
            limit = min(timeout, cfg.llm_timeout)
            with httpx.Client(
                transport=self.transport,
                timeout=httpx.Timeout(limit, connect=min(5, limit)),
                follow_redirects=False,
            ) as client:
                response = client.post(url, json=body, headers=headers)
                response.raise_for_status()
                if len(response.content) > 64000:
                    raise InvalidModelOutput("Tool-model response exceeded limits")
                payload = response.json()
            raw = (
                payload["message"]
                if cfg.llm_provider == "ollama"
                else payload["choices"][0]["message"]
            )
            return parse_turn(raw)
        except httpx.HTTPStatusError as exc:
            raise ModelUnavailable(f"Tool model HTTP {exc.response.status_code}") from None
        except httpx.HTTPError:
            raise ModelUnavailable("Tool model connection failed") from None
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise InvalidModelOutput("Invalid tool-model response") from exc
