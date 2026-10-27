"""Authenticated tenant-isolated Knowledge API with extractive cited answers."""

import json
import logging
import time
from dataclasses import dataclass
from typing import Annotated, Literal
from uuid import uuid4

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

from caseflow.answering import answer_question
from caseflow.auth import TOKEN_FORMAT, Principal, authenticate
from caseflow.chat import ChatModel, HttpChatModel, InvalidModelOutput, ModelUnavailable
from caseflow.config import Settings
from caseflow.database import EmbeddingModelMismatch, KnowledgeStore, connect
from caseflow.embeddings import Embeddings, FastEmbedAdapter, validate_vector
from caseflow.ingestion import Article, ingest_articles

log = logging.getLogger("caseflow.requests")
if not log.handlers:
    log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)
log.propagate = False
security = HTTPBearer(auto_error=False)


@dataclass
class Runtime:
    settings: Settings
    embeddings: Embeddings
    chat: ChatModel


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SearchBody(ApiModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: Annotated[StrictInt, Field(ge=1, le=20)] = 5

    @field_validator("query")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Query must not be blank")
        return value.strip()


class DocumentBody(ApiModel):
    id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=100)
    title: str = Field(min_length=1, max_length=200)
    source: str = Field(default="api", min_length=1, max_length=500)
    text: str = Field(min_length=1, max_length=20000)

    @field_validator("title", "source", "text")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Document fields must not be blank")
        return value


class IngestBody(ApiModel):
    documents: list[DocumentBody] = Field(min_length=1, max_length=20)


class SearchHit(ApiModel):
    id: str
    document_id: str
    position: int
    text: str
    title: str
    source: str
    score: float


class SearchResponse(ApiModel):
    results: list[SearchHit]


class Citation(ApiModel):
    chunk_id: str
    document_id: str
    title: str
    source: str
    quote: str


class AskResponse(ApiModel):
    found: bool
    answer: str
    citations: list[Citation]
    reason: Literal[
        "answered", "record_lookup_required", "no_evidence", "model_declined", "invalid_evidence"
    ]


def get_runtime(request: Request) -> Runtime:
    return request.app.state.runtime


def get_connection(runtime: Annotated[Runtime, Depends(get_runtime)]):
    with connect(runtime.settings) as conn:
        yield conn


Database = Annotated[psycopg.Connection, Depends(get_connection)]
AppRuntime = Annotated[Runtime, Depends(get_runtime)]


def get_bearer_token(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> str:
    if len(request.headers.getlist("authorization")) != 1 or credentials is None:
        raise HTTPException(401, "Invalid credentials", headers={"WWW-Authenticate": "Bearer"})
    if not TOKEN_FORMAT.fullmatch(credentials.credentials):
        raise HTTPException(401, "Invalid credentials", headers={"WWW-Authenticate": "Bearer"})
    return credentials.credentials


def get_principal(token: Annotated[str, Depends(get_bearer_token)], conn: Database) -> Principal:
    principal = authenticate(conn, token)
    if principal is None:
        raise HTTPException(401, "Invalid credentials", headers={"WWW-Authenticate": "Bearer"})
    return principal


Identity = Annotated[Principal, Depends(get_principal)]


def require(principal: Principal, scope: str) -> None:
    if scope not in principal.scopes:
        raise HTTPException(403, "Insufficient scope")


class BodyLimit:
    """Buffer a bounded request before JSON parsing; never log body or credentials."""

    def __init__(self, app, max_bytes=256000):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
            return await self.app(scope, receive, send)
        messages, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > self.max_bytes:
                return await JSONResponse({"detail": "Request body too large"}, status_code=413)(
                    scope, receive, send
                )
            messages.append(message)
            if not message.get("more_body", False):
                break
        iterator = iter(messages)

        async def replay():
            message = next(iterator, None)
            return message if message is not None else await receive()

        await self.app(scope, replay, send)


def create_app(runtime: Runtime | None = None) -> FastAPI:
    cfg = runtime.settings if runtime else Settings.from_env()
    app = FastAPI(title="CaseFlow Knowledge API", version="0.1.0")
    app.state.runtime = runtime or Runtime(cfg, FastEmbedAdapter(cfg), HttpChatModel(cfg))
    app.add_middleware(BodyLimit)

    @app.middleware("http")
    async def request_log(request: Request, call_next):
        request_id = uuid4().hex
        start = time.monotonic()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        route = request.scope.get("route")
        log.info(
            json.dumps(
                {
                    "event": "http_request",
                    "request_id": request_id,
                    "method": request.method,
                    "route": getattr(route, "path", "unmatched"),
                    "status": response.status_code,
                    "duration_ms": round((time.monotonic() - start) * 1000, 2),
                }
            )
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        errors = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
        return JSONResponse({"detail": errors}, status_code=422)

    @app.exception_handler(psycopg.Error)
    async def database_error(request, exc):
        return JSONResponse({"detail": "Database unavailable"}, status_code=503)

    @app.exception_handler(ModelUnavailable)
    async def model_error(request, exc):
        return JSONResponse({"detail": "Model unavailable"}, status_code=503)

    @app.exception_handler(InvalidModelOutput)
    async def model_output_error(request, exc):
        return JSONResponse({"detail": "Invalid model response"}, status_code=502)

    @app.exception_handler(EmbeddingModelMismatch)
    async def mismatched_model(request, exc):
        return JSONResponse(
            {"detail": "Stored embedding model mismatch; re-ingestion required"}, status_code=503
        )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/ready")
    def ready(conn: Database, runtime: AppRuntime):
        conn.execute("SELECT token_hash FROM api_tokens LIMIT 1")
        conn.execute("SELECT embedding FROM chunks LIMIT 1")
        try:
            validate_vector(runtime.embeddings.embed_query("readiness check"))
        except Exception as exc:
            raise HTTPException(503, "Embedding service unavailable") from exc
        return {"status": "ready", "checks": {"database": True, "embedding": True}}

    def search_rows(body, principal, conn, runtime):
        require(principal, "kb:read")
        try:
            vector = runtime.embeddings.embed_query(body.query)
        except Exception as exc:
            raise HTTPException(503, "Embedding service unavailable") from exc
        return KnowledgeStore(conn, runtime.embeddings.model_name).search(
            principal.tenant_id, vector, body.top_k
        )

    @app.post("/v1/search", response_model=SearchResponse)
    def search(
        body: SearchBody,
        principal: Identity,
        conn: Database,
        runtime: AppRuntime,
    ):
        return {"results": search_rows(body, principal, conn, runtime)}

    @app.post("/v1/ask", response_model=AskResponse)
    def ask(
        body: SearchBody,
        principal: Identity,
        conn: Database,
        runtime: AppRuntime,
    ):
        rows = search_rows(body, principal, conn, runtime)
        return answer_question(body.query, rows, runtime.chat, runtime.settings.min_similarity)

    @app.post("/v1/ingest")
    def ingest(
        body: IngestBody,
        principal: Identity,
        conn: Database,
        runtime: AppRuntime,
    ):
        require(principal, "kb:write")
        articles = [Article(d.id, d.title, d.source, d.text) for d in body.documents]
        try:
            return ingest_articles(
                KnowledgeStore(conn, runtime.embeddings.model_name),
                runtime.embeddings,
                principal.tenant_id,
                articles,
                runtime.settings.chunk_size,
                runtime.settings.chunk_overlap,
            )
        except ValueError as exc:
            raise HTTPException(422, "Invalid document batch or embedding configuration") from exc

    return app


app = create_app()
