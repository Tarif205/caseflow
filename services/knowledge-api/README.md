# Knowledge API

Implementation lives in `src/caseflow`. This service retrieves tenant-specific
help articles and lets a model select supporting quotations. The response contains
only validated source quotes, with citations.

## Start locally

In VS Code's PowerShell terminal, with Docker Desktop running:

```powershell
cd G:\caseflow
uv sync --frozen --cache-dir G:\uv-cache
docker compose up -d --wait db
uv run --frozen caseflow init-db
uv run --frozen caseflow provision-token --tenant northwind --scope kb:read --scope kb:write --env-name NORTHWIND_API_TOKEN
uv run --frozen caseflow provision-token --tenant contoso --scope kb:read --env-name CONTOSO_API_TOKEN
```

Provisioning appends generated credentials to the ignored `.env` without displaying
them; the database stores only SHA-256 hashes. Repeating the commands reuses matching
active credentials. Never share or commit token values. Existing `.env` settings
are preserved. These two demo tokens have already been provisioned on this machine.

For the hosted model used in the successful Day 4 check, keep the existing Groq key
in `.env` as `LLM_API_KEY`, then run these commands in the same terminal:

```powershell
$env:LLM_PROVIDER = 'openai_compatible'
$env:DOCKER_LLM_BASE_URL = 'https://api.groq.com/openai/v1'
$env:LLM_MODEL = 'openai/gpt-oss-20b'
docker compose up -d --build --wait knowledge-api
uv run --frozen python scripts/smoke_knowledge.py
```

Success: Docker reports the service healthy, then the script reports successful
checks and `live_model_tested: true`. Initial image and embedding downloads can take
several minutes; later starts reuse Docker's embedding cache. Model availability
and free-tier quotas must be checked before deployment. A hosted request consumes
the provider's quota; `--skip-model` checks transport, search and refusal only.

These PowerShell overrides last for that terminal session. Reapply them after
opening a new terminal before recreating the container. They do not modify `.env`.
With no overrides, Compose defaults to Ollama on the host using `qwen3:4b`; ensure
Ollama is running and sufficient RAM is available before using that configuration.
The Docker base URL uses `DOCKER_LLM_BASE_URL`; host Python uses `LLM_BASE_URL`.

Open http://localhost:8001/docs for the interactive API. Click **Authorize** and
enter only your token from `.env`, then try `/v1/ask` with:

```json
{"query": "How long is the manufacturing defect warranty?", "top_k": 5}
```

Expect `found: true`, a one-year warranty quotation, and a `warranty.md` citation.
Do not paste the token into chat, screenshots or issue reports.

## Routes

| Method and route | Access | Behavior |
|---|---|---|
| GET `/health` | Public | Process liveness; no database or model call |
| GET `/ready` | Public | Checks database tables and embedding availability |
| POST `/v1/search` | `kb:read` | Returns up to 20 tenant-filtered chunks |
| POST `/v1/ask` | `kb:read` | Returns verified quotations and citations, or a refusal reason |
| POST `/v1/ingest` | `kb:write` | Replaces supplied documents in the authenticated tenant |

Search and ask take `query` and optional `top_k`. Ingest takes `documents`, each
with `id`, `title`, `source` and `text`. Extra fields, including caller-supplied
tenant ids, are rejected. The token determines the tenant. Ingest permits at most
20 documents of 20,000 characters each, subject to a 256,000-byte request limit.
The local admin CLI bypasses HTTP authentication and must remain trusted.

Startup migrates the local schema and seeds only empty tenant corpora. It preserves
existing articles and API edits. Explicit admin ingestion replaces supplied articles.
The API listens on loopback port 8001; Postgres listens on loopback port 5432.

## Limits and verification

The operating setting remains 800-character chunks, 120 overlap, top-5 and a
provisional minimum similarity of 0.691243. Source validation prevents invented
quotations and citations to unprovided chunks; it does not prove that a quotation
fully answers a question. There is no held-out generated-answer quality benchmark.
Concrete order references are refused because this service has policies, not live
orders. The later support agent will use order tools.

`/ready` does not check live chat-model availability or quota. Provider errors are
reported without upstream bodies or secrets. Request logs record ids, route,
duration and status rather than prompts or authorization headers. The Docker image
runs as an unprivileged user and excludes `.env`. This local service is not yet
configured for public traffic, TLS, rate limiting or production authorization policy.

Evidence: [live smoke](../../evals/results/day-04-api-smoke.json),
[transport check](../../evals/results/day-04-api-transport.json), and
[technical record](../../docs/journal/day-04.md). CI runs tests with a separate local
Postgres service and builds the image; a GitHub run is pending the user's push.

Stop the services without deleting data:

```powershell
docker compose stop knowledge-api db
```
