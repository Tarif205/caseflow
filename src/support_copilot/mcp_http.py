"""Stateless Streamable HTTP with explicit per-request demo bearer authorization.

This reuses pre-provisioned project tokens; it does not implement OAuth discovery,
issuance or third-party-client authorization. No reusable MCP sessions exist.
"""

import json
import logging
import os
import re
import time
from contextlib import asynccontextmanager
from urllib.parse import urlsplit
from uuid import uuid4

import anyio
import psycopg
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from support_copilot.auth import authenticate
from support_copilot.database import connect
from support_copilot.mcp_server import CONTRACTS, MCPReads, create_server, runtime_settings

READ_SCOPES = {"kb:read", "orders:read", "tickets:read"}
AUTH_PATTERN = re.compile(r"Bearer ([A-Za-z0-9_-]{32,128})", re.IGNORECASE)


class HTTPGateway:
    def __init__(self, cfg, manager, hosts, origins):
        self.cfg, self.manager, self.hosts, self.origins = cfg, manager, set(hosts), set(origins)

    async def __call__(self, scope, receive, send):
        started = time.monotonic()
        status = 500
        request_id = uuid4().hex

        async def record(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                message["headers"].append((b"x-request-id", request_id.encode()))
            await send(message)

        try:
            await self.handle(scope, receive, record)
        finally:
            logging.getLogger("support_copilot.mcp.requests").info(
                json.dumps(
                    {
                        "event": "mcp_request",
                        "request_id": request_id,
                        "method": scope["method"],
                        "status": status,
                        "duration_ms": round((time.monotonic() - started) * 1000, 2),
                    }
                )
            )

    async def handle(self, scope, receive, send):
        async def reject(status, error, auth=False):
            headers = {"WWW-Authenticate": "Bearer"} if auth else None
            await JSONResponse({"error": error}, status_code=status, headers=headers)(
                scope, receive, send
            )

        def headers(name):
            return [
                value.decode("latin1") for key, value in scope["headers"] if key.lower() == name
            ]

        host = headers(b"host")
        try:
            url = urlsplit("//" + host[0]) if len(host) == 1 else None
            valid = (
                url is not None
                and url.hostname in self.hosts
                and not url.username
                and not url.password
                and not url.path
                and not url.query
                and not url.fragment
            )
            if url is not None:
                _port = url.port  # Reject malformed/non-numeric ports before SDK checks.
        except ValueError:
            valid = False
        if not valid:
            return await reject(421, "invalid_host")
        origin = headers(b"origin")
        if len(origin) > 1 or origin and origin[0] not in self.origins:
            return await reject(403, "invalid_origin")
        authorization = headers(b"authorization")
        match = AUTH_PATTERN.fullmatch(authorization[0]) if len(authorization) == 1 else None
        if match is None:
            return await reject(401, "invalid_credentials", True)
        token = match[1]

        def identity():
            with connect(self.cfg, read_only=True) as conn:
                return authenticate(conn, token)

        try:
            actor = await anyio.to_thread.run_sync(identity)
        except psycopg.Error:
            return await reject(503, "service_unavailable")
        if actor is None:
            return await reject(401, "invalid_credentials", True)
        if not READ_SCOPES & actor.scopes:
            return await reject(403, "insufficient_scope", True)
        if scope.get("query_string") or headers(b"mcp-session-id"):
            return await reject(400, "stateless_endpoint_accepts_no_query_or_session_id")
        if scope["method"] != "POST":
            return await JSONResponse(
                {"error": "method_not_allowed"}, status_code=405, headers={"Allow": "POST"}
            )(scope, receive, send)
        content_type = headers(b"content-type")
        if (
            len(content_type) != 1
            or content_type[0].split(";")[0].strip().lower() != "application/json"
        ):
            return await reject(400, "invalid_content_type")
        body = bytearray()
        while True:
            part = await receive()
            if part["type"] == "http.disconnect":
                return
            chunk = part.get("body", b"")
            if len(body) + len(chunk) > 16384:
                return await reject(413, "request_too_large")
            body.extend(chunk)
            if not part.get("more_body", False):
                break
        try:
            payload = json.loads(body)
            if not isinstance(payload, dict) or not isinstance(payload.get("method"), str):
                raise ValueError
            params = payload.get("params") or {}
            if not isinstance(params, dict):
                raise ValueError
        except (ValueError, TypeError):
            return await reject(400, "invalid_message")
        required = None
        if payload["method"] == "tools/call" and isinstance(params.get("name"), str):
            contract = CONTRACTS.get(params["name"])
            required = contract[2] if contract else None
        elif payload["method"] in {"resources/read", "prompts/get"}:
            required = "kb:read"
        if required and required not in actor.scopes:
            return await reject(403, "insufficient_scope", True)
        # The SDK attaches this exact Request to each message's request context.
        # It is not a global token and is never inferred from a session id.
        scope["mcp_token"] = token
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        return await self.manager.handle_request(scope, replay, send)


def create_app(settings=None, *, embeddings=None, allowed_hosts=None, allowed_origins=None):
    cfg = settings or runtime_settings()
    hosts = (
        allowed_hosts
        if allowed_hosts is not None
        else os.getenv("MCP_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    )
    origins = (
        allowed_origins
        if allowed_origins is not None
        else os.getenv("MCP_ALLOWED_ORIGINS", "http://127.0.0.1:6274,http://localhost:6274").split(
            ","
        )
    )
    hosts = [h.strip() for h in hosts if h.strip()]
    origins = [o.strip() for o in origins if o.strip()]
    if not hosts or any("*" in value for value in hosts + origins):
        raise ValueError("Use explicit MCP hosts and origins")
    reads = MCPReads(cfg, "", embeddings)
    server = create_server(reads)
    reads._token_source = lambda: server.request_context.request.scope.get("mcp_token", "")
    security = TransportSecuritySettings(
        allowed_hosts=[item for h in hosts for item in (h, h + ":*")], allowed_origins=origins
    )
    manager = StreamableHTTPSessionManager(
        server,
        stateless=True,
        json_response=True,
        security_settings=security,
        max_request_body_size=16384,
    )
    logger = logging.getLogger("support_copilot.mcp.requests")
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    logger.propagate = False

    @asynccontextmanager
    async def lifespan(app):
        async with manager.run():
            yield

    async def health(request):
        return JSONResponse({"status": "ok"})

    async def ready(request):
        def check():
            with connect(cfg, read_only=True) as conn:
                conn.execute("SELECT 1").fetchone()

        try:
            await anyio.to_thread.run_sync(check)
        except psycopg.Error:
            return JSONResponse({"status": "unavailable"}, status_code=503)
        return JSONResponse({"status": "ready", "transport": "streamable-http", "stateless": True})

    return Starlette(
        routes=[
            Route("/health", health),
            Route("/ready", ready),
            Route(
                "/mcp", HTTPGateway(cfg, manager, hosts, origins), methods=["POST", "GET", "DELETE"]
            ),
        ],
        lifespan=lifespan,
    )


app = create_app()
