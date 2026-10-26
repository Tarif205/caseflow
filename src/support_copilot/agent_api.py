"""Authenticated support workflow. Tenant and authority come only from bearer auth."""

import json
import logging
import os
import time
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

import httpx
import psycopg
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from support_copilot.agent_graph import GraphModel
from support_copilot.agent_tools import BoundTools
from support_copilot.approvals import ApprovalDenied, ApprovalStore
from support_copilot.auth import TOKEN_FORMAT, authenticate
from support_copilot.config import Settings
from support_copilot.database import connect
from support_copilot.durable_agent import DurableAgent
from support_copilot.tracing import TraceRecorder


class StartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticket_id: str = Field(min_length=1, max_length=80)


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    approved: StrictBool


def create_app(settings=None, *, agent_factory=None):
    cfg = settings or Settings.from_env()
    app = FastAPI(title="Fictional support agent", root_path=os.getenv("AGENT_ROOT_PATH", ""))
    bearer = HTTPBearer(auto_error=False)
    logger = logging.getLogger("support_copilot.agent.requests")
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    logger.propagate = False

    @app.middleware("http")
    async def log_request(request, call_next):
        if (
            request.headers.get("content-length", "").isdigit()
            and int(request.headers["content-length"]) > 4096
        ):
            return JSONResponse(status_code=413, content={"detail": "Request too large"})
        # Bound chunked bodies too, before Pydantic parses them.
        if request.method == "POST":
            raw = bytearray()
            async for chunk in request.stream():
                raw.extend(chunk)
                if len(raw) > 4096:
                    return JSONResponse(status_code=413, content={"detail": "Request too large"})
            request._body = bytes(raw)
            request.scope["agent_body_present"] = bool(raw)
        started = time.monotonic()
        response = await call_next(request)
        request_id = uuid4().hex
        response.headers["X-Request-ID"] = request_id
        logger.info(
            json.dumps(
                {
                    "event": "agent_request",
                    "request_id": request_id,
                    "route": getattr(request.scope.get("route"), "path", "unmatched"),
                    "status": response.status_code,
                    "duration_ms": round((time.monotonic() - started) * 1000, 2),
                }
            )
        )
        return response

    def identity(
        request: Request,
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    ):
        if (
            len(request.headers.getlist("authorization")) != 1
            or not credentials
            or not TOKEN_FORMAT.fullmatch(credentials.credentials)
        ):
            raise HTTPException(401, "Invalid credentials")
        with connect(cfg) as conn:
            actor = authenticate(conn, credentials.credentials)
        if actor is None:
            raise HTTPException(401, "Invalid credentials")
        return actor, credentials.credentials

    Identity = Annotated[tuple, Depends(identity)]

    def agent(auth):
        actor, token = auth
        if "agent:run" not in actor.scopes:
            raise HTTPException(403, "Insufficient permissions")
        if agent_factory:
            return agent_factory(actor, token)
        tools = BoundTools(
            actor,
            os.getenv("KNOWLEDGE_API_URL", "http://127.0.0.1:8001"),
            os.getenv("MOCK_BACKEND_URL", "http://127.0.0.1:8004"),
            token,
            token,
            allow_internal=True,
        )

        def execute(run_id):
            try:
                with httpx.Client(timeout=20, follow_redirects=False) as client:
                    response = client.post(
                        tools.backend_url + "/refunds",
                        json={"run_id": run_id},
                        headers={"Authorization": "Bearer " + token},
                    )
                    response.raise_for_status()
                    receipt = response.json()
                if (
                    not isinstance(receipt, dict)
                    or type(receipt.get("amount_cents")) is not int
                    or not isinstance(receipt.get("order_id"), str)
                ):
                    raise ApprovalDenied("Invalid refund receipt")
                return receipt
            except (httpx.HTTPError, ValueError):
                raise ApprovalDenied("Mock refund not authorized or unavailable") from None

        tracer = TraceRecorder()
        if os.getenv("AGENT_TRACING_ENABLED") == "true":
            from langfuse import get_client

            tracer = TraceRecorder(get_client())
        return DurableAgent(
            cfg,
            GraphModel(cfg),
            tools,
            Path(".cache/unused.sqlite"),
            tracer,
            checkpoint_backend="postgres",
            executor=execute,
        )

    @app.exception_handler(ApprovalDenied)
    async def denied(request, exc):
        return JSONResponse(
            status_code=403, content={"detail": "Operation not authorized or not ready"}
        )

    @app.exception_handler(psycopg.Error)
    async def unavailable(request, exc):
        return JSONResponse(status_code=503, content={"detail": "Service unavailable"})

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/ready")
    def ready():
        with connect(cfg) as conn:
            row = conn.execute("SELECT to_regclass('checkpoints') IS NOT NULL AS ready").fetchone()
        if not row["ready"]:
            raise HTTPException(503, "Service not initialized")
        return {"status": "ready", "checkpoint_backend": "postgres"}

    @app.post("/runs")
    def start(payload: StartRequest, auth: Identity, request: Request):
        if request.query_params:
            raise HTTPException(422, "Unexpected query fields")
        return agent(auth).start(payload.ticket_id)

    @app.get("/runs/{run_id}")
    def status(run_id: UUID, auth: Identity):
        return agent(auth).status(str(run_id))

    @app.post("/runs/{run_id}/resume")
    def resume(run_id: UUID, auth: Identity, request: Request):
        if request.query_params or request.scope.get("agent_body_present"):
            raise HTTPException(422, "Resume accepts no approval payload")
        return agent(auth).resume(str(run_id))

    @app.get("/approvals")
    def pending(auth: Identity):
        with connect(cfg) as conn:
            return {"pending": ApprovalStore(conn).pending(auth[0])}

    @app.post("/approvals/{run_id}/decision")
    def decide(run_id: UUID, payload: DecisionRequest, auth: Identity, request: Request):
        if request.query_params:
            raise HTTPException(422, "Unexpected query fields")
        with connect(cfg) as conn:
            ApprovalStore(conn).decide(auth[0], str(run_id), payload.approved)
        return {"run_id": str(run_id), "decision": "approved" if payload.approved else "rejected"}

    return app


app = create_app()
