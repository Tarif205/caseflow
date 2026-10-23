# Support Copilot Platform

A small support system for fictional Northwind Outfitters, using RAG, LangGraph, MCP, Docker and Postgres with pgvector. Local development uses free tools. All examples are fictional.

**Status:** Day 4 Knowledge API works locally in Docker: scoped token authentication, tenant-filtered search, ingestion and answers with verified source quotes. A real hosted-model answer passed the end-to-end smoke check; 143 automated tests passed. GitHub CI passed for user-pushed commit `3d0bd84`. The user prepared EC2 and built that revision's image there; the cloud API has not yet started. The support agent, MCP server and public deployment remain pending. Learning checks remain deferred; no completed sprint gate or independent mastery is claimed.

For an explanation from the beginning, read [Project explained](docs/PROJECT_EXPLAINED.md).
For official topic names, exercises and video resources, use the
[Learning roadmap](docs/LEARNING_ROADMAP.md).

## Services

| Service | What it does | Status |
|---------|--------------|--------|
| `services/knowledge-api` | Ingests help-center articles and answers questions with citations (RAG) | Working locally; [setup and endpoints](services/knowledge-api/README.md) |
| `services/mock-backend` | Fictional orders, tickets and refunds for two tenants | Not started |
| `services/support-agent` | LangGraph agent that drafts replies and pauses for human approval before a refund | Not started |
| `services/mcp-server` | Read-only MCP tools with token auth and tenant isolation | Not started |

## Repository layout

```
docs/      architecture, decisions, journal, debug log
data/      Northwind help-center articles, mock orders
evals/     retrieval/, agent/, mcp/ datasets and scripts; results/
services/  the four services above
src/       shared Python implementation
compose.yaml  local Knowledge API and Postgres with pgvector
infra/     deployment notes and later configuration
```

## Running it

For the complete HTTP service, follow the [Knowledge API setup](services/knowledge-api/README.md).
Its interactive API documentation is at http://localhost:8001/docs while running.
The commands below exercise the database and retrieval components directly.

Use Windows PowerShell in `G:\support-copilot`, with Docker Desktop running:

```powershell
cd G:\support-copilot
uv sync --frozen --cache-dir G:\uv-cache
docker compose up -d --wait db
uv run --frozen copilot init-db
uv run --frozen copilot check-search --output evals/results/day-01-search.json
```

`init-db` creates the vector extension and initial tables without dropping existing data.
`check-search` inserts or replaces three Day 1 demo articles under `northwind-day1-demo`, then embeds
five questions and runs raw SQL cosine-distance search. It does not call a chat model.
Expect `top1_accuracy: 1.0` on this small check. It is not the later 40-question evaluation.

The local-only database uses the public demo credentials in `compose.yaml`, binds to
`127.0.0.1:5432`, has a health check and a 384 MB memory limit. Its data survives container
restarts in the Docker volume `support-copilot_dbdata`. Do not use these credentials for
deployment or expose this database to the internet.

An empty or missing `DATABASE_URL` selects this local database. A nonempty value overrides
it; `NEON_DATABASE_URL` is deliberately not selected automatically. The embedding cache
defaults to `G:\fastembed-cache` on Windows and `.cache/fastembed` on Linux. Set
`FASTEMBED_CACHE_PATH` to override it. The configured model must produce 384 dimensions.

### Import the help center

```powershell
uv run --frozen copilot ingest --tenant northwind --directory data/northwind
uv run --frozen copilot ingest --tenant contoso --directory data/contoso
```

The default 800-character chunks with 120-character overlap produce 30 chunks for
Northwind's 15 articles and 6 chunks for Contoso's 3 articles. Each embedding includes
the article title as context. Original chunk text is preserved for later citations.
Imports replace only the supplied documents in the specified tenant. Re-importing
does not append duplicates; no missing-file deletions are performed automatically.
This CLI is a trusted local admin command, not an authenticated public ingest API.

To reproduce the two-pass import, count, stable-id and tenant-isolation check:

```powershell
uv run --frozen python evals/retrieval/check_ingestion.py --output evals/results/day-02-ingestion.json
```

That script refuses remote databases and uses only the local `copilot` development
database. See [data documentation](data/README.md) and the
[chunking decision](docs/decisions/001-chunking.md) for corpus and import semantics.

Stop the local database when finished:

```powershell
docker compose stop db
```

### Tests

Unit tests use fake embeddings and do not download a model or call a hosted service:

```powershell
uv run --frozen pytest -q -m "not integration"
uv run --frozen ruff check src tests scripts evals/retrieval
uv run --frozen ruff format --check src tests scripts evals/retrieval
```

For integration tests, create a separate local database once:

```powershell
docker compose exec -T db createdb -U copilot copilot_test
$env:TEST_DATABASE_URL = 'postgresql://copilot:copilot-local-only@127.0.0.1:5432/copilot_test'
uv run --frozen pytest -q
```

If `copilot_test` already exists, skip `createdb`. Integration tests reject remote hosts and
database names other than `copilot_test`; test data is rolled back after each test.
Without `TEST_DATABASE_URL`, these tests explicitly skip rather than pretend to pass.

## Results

The recorded [Day 1 search sanity check](evals/results/day-01-search.json) returned the
expected article first for all five questions over a three-article corpus. This is a
small setup check, not evidence of production retrieval quality. Agent evaluations and a
full generated-answer benchmark remain pending.

The [Day 2 ingestion check](evals/results/day-02-ingestion.json) verified identical
chunk ids, source text and counts after two imports with real embeddings. Search
results for each tenant were checked against that tenant's original source files.
The [Day 3 development results](evals/results/day-03-retrieval.md) compare five
configurations using 40 answerable and 10 unanswerable synthetic questions. Run:

```powershell
uv run --frozen python evals/retrieval/run.py
```

All configurations found the expected article within five chunks on this set.
Larger chunks improved MRR@5 from 0.950 to 1.000 and top-1 article accuracy from
90% to 100%. Those labels are assistant-authored and have not been independently
reviewed; configurations and thresholds were tuned on the same set. These are
development results, not a held-out benchmark or evidence of generated-answer quality.

Score thresholds rejected 9/10 unanswerable questions, but at the larger-chunk
threshold also rejected 5/40 answerable ones. An exact refund-date question still
passed despite the answer not being in the corpus. The Day 2 importer defaults remain
unchanged until API-level evaluation. See [evaluation methodology](evals/retrieval/README.md).

| Metric | Result | Date |
|--------|--------|------|
| Day 1 sanity check top-1 accuracy (5 questions, 3 articles) | 5/5 | 2026-10-22 |
| Full corpus import | 18 documents / 36 chunks | 2026-10-22 |
| Repeat import | Identical ids, text and counts | 2026-10-22 |
| Automated tests including local Postgres integration | 144 passed | 2026-10-23 |
| Docker API smoke check with real hosted model | Cited warranty answer, auth, isolation and order refusal passed | 2026-10-22 |
| Retrieval Recall@5 (40 synthetic development questions) | 1.000 | 2026-10-22 |
| MRR@5 baseline / larger chunks | 0.950 / 1.000 | 2026-10-22 |
| Larger-chunk score gate: unanswerable rejection / answerable acceptance | 90% / 87.5% (in-sample) | 2026-10-22 |
| Agent scenarios completed (25) | Not run | |
| Refund attempts that paused for approval | Not implemented | |
| Cross-tenant leaks in MCP tests | MCP not implemented | |

## Configuration

Use `.env.example` as a reference for setting names. Preserve an existing `.env`; do not
overwrite it with the example. `.env` is ignored and must never be committed. Database
credentials are excluded from settings representations and CLI driver error messages.

Tenant isolation currently relies on mandatory parameterized filters in the application
queries and composite database foreign keys. This initial schema does not implement
Postgres row-level security; clients must never receive database credentials. API tokens
are stored as hashes and bind the caller to one tenant and explicit scopes. See the
[Day 4 evidence and limitations](docs/journal/day-04.md).

## Next implementation step

Day 5: prepare a zero-budget public deployment and verify the deployed service.
Check current free-tier terms before provisioning anything. Git commits and pushes
remain the user's responsibility; GitHub CI passed for commit `3d0bd84`.
Preparation: [AWS account and rollout](docs/deploy-aws.md), or the PRD's
[Free Render fallback](docs/deploy-render.md) using `render.yaml`. Neither route
has a verified public API deployment. AWS account access, server setup and image
build are complete; hosted database preparation and public smoke checks are pending.
