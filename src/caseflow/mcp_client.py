"""Bounded MCP read adapter for the existing synchronous LangGraph workflow.

Identity, URL and allowed schemas are bound by the host, never by the model.
There is deliberately no refund/approval RPC or direct-HTTP fallback here.
"""

import json
import math
from dataclasses import dataclass, field

import anyio
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from caseflow.agent_tools import RecordNotFound, ToolFailure, safe_base_url
from caseflow.auth import TOKEN_FORMAT, Principal
from caseflow.mcp_server import CONTRACTS

NAMES = {"search_kb": "search_knowledge_base", "get_order": "get_order_status"}
MAX_RESPONSE_BYTES = 128_000


@dataclass
class MCPTools:
    principal: Principal
    url: str
    token: str = field(repr=False)
    transport: object = field(default=None, repr=False)
    allow_internal: bool = False

    def __post_init__(self):
        self.url = safe_base_url(self.url, allow_internal=self.allow_internal)
        if not self.url.endswith("/mcp") or not TOKEN_FORMAT.fullmatch(self.token):
            raise ValueError("Configure an MCP endpoint and active credential")

    async def _invoke(self, name, arguments, timeout):
        async def bounded_response(response):
            # JSON response mode only; do not allocate an unbounded server response.
            data = bytearray()
            async for chunk in response.aiter_bytes():
                if len(data) + len(chunk) > MAX_RESPONSE_BYTES:
                    raise ToolFailure("MCP response exceeded limits")
                data.extend(chunk)
            response._content = bytes(data)
            if response.status_code == 202 and not data:
                return  # Initialized notifications have an empty accepted response.
            if response.headers.get("content-type", "").split(";")[0] != "application/json":
                raise ToolFailure("Invalid MCP response")

        async with httpx.AsyncClient(
            headers={"Authorization": "Bearer " + self.token},
            transport=self.transport,
            follow_redirects=False,
            timeout=timeout,
            event_hooks={"response": [bounded_response]},
        ) as client:
            async with streamable_http_client(self.url, http_client=client) as (
                read,
                write,
                session_id,
            ):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    if session_id() is not None:
                        raise ToolFailure("Unexpected MCP session")
                    definitions = (await session.list_tools()).tools
                    names = [tool.name for tool in definitions]
                    if len(names) != len(set(names)) or set(names) != set(CONTRACTS):
                        raise ToolFailure("Unexpected MCP tool registry")
                    for tool in definitions:
                        inputs, outputs, _, _ = CONTRACTS[tool.name]
                        if (
                            tool.inputSchema != inputs.model_json_schema()
                            or tool.outputSchema != outputs.model_json_schema()
                            or tool.annotations is None
                            or tool.annotations.readOnlyHint is not True
                            or tool.annotations.destructiveHint is not False
                        ):
                            raise ToolFailure("MCP schema contract changed")
                    result = await session.call_tool(name, arguments)
                    if result.isError:
                        # Server-authored generic code only; never echo arbitrary text.
                        for part in result.content:
                            if part.type == "text":
                                try:
                                    value = json.loads(part.text)
                                except (ValueError, TypeError):
                                    continue
                                if isinstance(value, dict) and value.get("code") == "not_found":
                                    raise RecordNotFound("Record not found")
                        raise ToolFailure("MCP read unavailable")
                    return (
                        CONTRACTS[name][1]
                        .model_validate(result.structuredContent)
                        .model_dump(mode="json")
                    )

    def execute(self, name: str, args: dict, timeout: float) -> dict:
        remote_name = NAMES.get(name)
        if remote_name is None:
            raise ToolFailure("Tool unavailable")
        inputs, _, scope, _ = CONTRACTS[remote_name]
        checked = inputs.model_validate(args)
        if scope not in self.principal.scopes:
            raise ToolFailure("Insufficient tool scope")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ToolFailure("MCP deadline exceeded")

        async def run():
            with anyio.fail_after(min(timeout, 20)):
                return await self._invoke(remote_name, checked.model_dump(), min(timeout, 20))

        try:
            return anyio.run(run)
        except Exception as exc:
            # AnyIO's task groups can wrap a clean not-found in ExceptionGroup.
            def not_found(error):
                if isinstance(error, BaseExceptionGroup):
                    return bool(error.exceptions) and all(not_found(e) for e in error.exceptions)
                return isinstance(error, RecordNotFound)

            if not_found(exc):
                raise RecordNotFound("Record not found") from None
            raise ToolFailure("MCP read unavailable") from None
