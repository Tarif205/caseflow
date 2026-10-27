"""One bounded HTTP call to Ollama or an OpenAI-compatible provider."""

import json
import math
import re
from typing import Protocol
from urllib.parse import urlparse

import httpx

from caseflow.config import Settings


class ModelUnavailable(RuntimeError):
    def __init__(self, message, *, diagnostic=None):
        super().__init__(message)
        self.diagnostic = diagnostic or {}


class InvalidModelOutput(RuntimeError):
    def __init__(self, message, *, diagnostic=None):
        super().__init__(message)
        self.diagnostic = diagnostic or {}


class ChatModel(Protocol):
    def complete_json(self, messages: list[dict]) -> dict: ...


def parse_json_reply(text: str) -> dict:
    if len(text) > 32000:
        raise InvalidModelOutput("Model output exceeded its limit")
    # Older local models may leak a thinking preamble despite think=false.
    if "</think>" in text:
        text = text.rsplit("</think>", 1)[-1]
    text = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, TypeError) as exc:
        raise InvalidModelOutput("Model did not return valid JSON") from exc
    if not isinstance(value, dict):
        raise InvalidModelOutput("Model output must be a JSON object")
    return value


class HttpChatModel:
    def __init__(self, settings: Settings, transport=None):
        self.settings = settings
        self.transport = transport

    def complete_json(
        self, messages: list[dict], *, schema=None, max_tokens=600, reasoning_effort=None
    ) -> dict:
        cfg = self.settings
        if cfg.llm_provider not in {"ollama", "openai_compatible"}:
            raise ModelUnavailable("Unsupported model provider")
        parsed = urlparse(cfg.llm_base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ModelUnavailable("Invalid model configuration")
        headers = {"Content-Type": "application/json"}
        if cfg.llm_provider == "ollama":
            url = cfg.llm_base_url + "/api/chat"
            body = {
                "model": cfg.llm_model,
                "messages": messages,
                "stream": False,
                "think": False,
                "format": schema or "json",
                "keep_alive": "0",
                "options": {"temperature": 0, "num_predict": 600, "num_ctx": 4096},
            }
        else:
            if not cfg.llm_api_key:
                raise ModelUnavailable("Model credentials are missing")
            if parsed.scheme != "https" and parsed.hostname not in {
                "localhost",
                "127.0.0.1",
                "::1",
            }:
                raise ModelUnavailable("Hosted model credentials require HTTPS")
            url = cfg.llm_base_url + "/chat/completions"
            headers["Authorization"] = f"Bearer {cfg.llm_api_key}"
            body = {
                "model": cfg.llm_model,
                "messages": messages,
                "temperature": 0,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            }
            if schema and cfg.llm_model.startswith("openai/gpt-oss-"):
                body["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {"name": "support_result", "strict": True, "schema": schema},
                }
            if reasoning_effort and cfg.llm_model.startswith("openai/gpt-oss-"):
                body["reasoning_effort"] = reasoning_effort
        try:
            with httpx.Client(
                timeout=cfg.llm_timeout, transport=self.transport, follow_redirects=False
            ) as client:
                response = client.post(url, json=body, headers=headers)
                response.raise_for_status()
                if len(response.content) > 64000:
                    raise InvalidModelOutput(
                        "Model response exceeded limit", diagnostic={"kind": "response_limit"}
                    )
                payload = response.json()
            if cfg.llm_provider == "ollama":
                content = payload["message"]["content"]
            else:
                if payload["choices"][0].get("finish_reason") == "length":
                    raise InvalidModelOutput(
                        "Model output truncated", diagnostic={"kind": "token_limit"}
                    )
                content = payload["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise InvalidModelOutput("Missing text in model response")
            return parse_json_reply(content)
        except httpx.HTTPStatusError as exc:
            diagnostic = {"kind": "http_error", "http_status": exc.response.status_code}
            try:
                wait = float(exc.response.headers.get("retry-after", "nan"))
                if math.isfinite(wait) and 0 < wait <= 300:
                    diagnostic["retry_after_seconds"] = wait
            except ValueError:
                pass
            try:
                code = exc.response.json().get("error", {}).get("code")
            except (ValueError, AttributeError):
                code = None
            if isinstance(code, str) and code in {
                "json_validate_failed",
                "tool_use_failed",
                "rate_limit_exceeded",
                "context_length_exceeded",
            }:
                diagnostic["code"] = code
            if code == "json_validate_failed":
                raise InvalidModelOutput(
                    "Provider JSON validation failed", diagnostic=diagnostic
                ) from None
            raise ModelUnavailable("Model request failed", diagnostic=diagnostic) from None
        except httpx.TimeoutException:
            raise ModelUnavailable(
                "Model request timed out", diagnostic={"kind": "timeout"}
            ) from None
        except httpx.HTTPError as exc:
            # Never expose an upstream URL, auth header or response body to clients/logs.
            raise ModelUnavailable(
                "Model request failed", diagnostic={"kind": "connection"}
            ) from exc
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise InvalidModelOutput("Unexpected model response") from exc
