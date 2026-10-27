FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.12-slim
RUN useradd --create-home --uid 10001 app && mkdir -p /cache/fastembed && chown app:app /cache/fastembed
WORKDIR /app
COPY --from=builder --chown=app:app /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" CASEFLOW_PROJECT_ROOT=/app FASTEMBED_CACHE_PATH=/cache/fastembed PYTHONUNBUFFERED=1
USER app
EXPOSE 8000
CMD ["uvicorn", "caseflow.mcp_http:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
