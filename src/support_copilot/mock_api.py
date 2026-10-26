"""Internal mock API. No refund can execute in the Day 6 implementation."""

import json
import logging
import os
import time
from typing import Annotated
from uuid import UUID, uuid4

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, ValidationError
from starlette.concurrency import run_in_threadpool

from support_copilot.approvals import ApprovalDenied, ApprovalStore
from support_copilot.auth import TOKEN_FORMAT, Principal, authenticate
from support_copilot.config import Settings
from support_copilot.database import connect
from support_copilot.mock_backend import MockStore


class RefundRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: UUID


def create_app(settings: Settings | None = None, *, enable_refunds=None) -> FastAPI:
    cfg = settings or Settings.from_env()
    app = FastAPI(title="Fictional internal mock backend")
    refunds_enabled = (
        enable_refunds
        if enable_refunds is not None
        else os.getenv("MOCK_REFUNDS_ENABLED") == "true"
    )
    bearer = HTTPBearer(auto_error=False)

    def database():
        with connect(cfg) as conn:
            yield conn

    Database = Annotated[psycopg.Connection, Depends(database)]

    def token(
        request: Request,
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    ) -> str:
        if (
            len(request.headers.getlist("authorization")) != 1
            or credentials is None
            or not TOKEN_FORMAT.fullmatch(credentials.credentials)
        ):
            raise HTTPException(401, "Invalid credentials", headers={"WWW-Authenticate": "Bearer"})
        return credentials.credentials

    Token = Annotated[str, Depends(token)]

    def identity(token: Token, conn: Database) -> Principal:
        principal = authenticate(conn, token)
        if principal is None:
            raise HTTPException(401, "Invalid credentials", headers={"WWW-Authenticate": "Bearer"})
        return principal

    Identity = Annotated[Principal, Depends(identity)]

    logger = logging.getLogger("support_copilot.mock.requests")
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    logger.propagate = False

    @app.middleware("http")
    async def request_log(request, call_next):
        started = time.monotonic()
        response = await call_next(request)
        request_id = uuid4().hex
        response.headers["X-Request-ID"] = request_id
        logger.info(
            json.dumps(
                {
                    "event": "mock_request",
                    "request_id": request_id,
                    "method": request.method,
                    "route": getattr(request.scope.get("route"), "path", "unmatched"),
                    "status": response.status_code,
                    "duration_ms": round((time.monotonic() - started) * 1000, 2),
                }
            )
        )
        return response

    def require(principal, scope):
        if scope not in principal.scopes:
            raise HTTPException(403, "Insufficient permissions")

    @app.exception_handler(psycopg.Error)
    async def db_error(request, exc):
        return JSONResponse(status_code=503, content={"detail": "Backend unavailable"})

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/orders/{order_id}")
    def order(order_id: str, request: Request, principal: Identity, conn: Database):
        require(principal, "orders:read")
        if request.query_params:
            raise HTTPException(422, "Unexpected query fields")
        row = MockStore(conn).get_order(principal.tenant_id, order_id)
        if row is None:
            raise HTTPException(404, "Record not found")
        return row

    @app.get("/tickets")
    def tickets(
        request: Request,
        principal: Identity,
        conn: Database,
        limit: Annotated[int, Query(ge=1, le=50)] = 10,
    ):
        require(principal, "tickets:read")
        if set(request.query_params) - {"limit"}:
            raise HTTPException(422, "Unexpected query fields")
        return {"tickets": MockStore(conn).open_tickets(principal.tenant_id, limit)}

    @app.post("/refunds")
    async def refunds(request: Request, principal: Identity, conn: Database):
        # Approval records and execution arrive later. A model or caller-supplied
        # approved=true flag must never activate a write route prematurely.
        if not refunds_enabled:
            raise HTTPException(501, "Refund execution is not enabled")
        require(principal, "refunds:execute")
        if request.query_params:
            raise HTTPException(422, "Unexpected query fields")
        body = bytearray()
        async for part in request.stream():
            body.extend(part)
            if len(body) > 4096:
                raise HTTPException(413, "Request too large")
        try:
            proposal = RefundRequest.model_validate_json(bytes(body))
        except ValidationError:
            raise HTTPException(422, "Invalid refund request") from None
        try:
            return await run_in_threadpool(
                ApprovalStore(conn).execute, principal, str(proposal.run_id)
            )
        except ApprovalDenied:
            raise HTTPException(403, "Refund not authorized") from None

    return app


app = create_app()
