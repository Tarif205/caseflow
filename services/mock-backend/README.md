# CaseFlow internal mock backend

**Current deployment:** release bb7491d uses the internal backend with guarded
mock refunds enabled. It has no published host port. A separate operator's durable
approval, current order facts, worker authority, policy and unique receipt are
rechecked on execution. The request supplies an approved run ID, not an amount
or an approval flag. No real commerce system is connected.

Start it with the [root README's full Compose setup](../../README.md).
The public MCP-backed synthetic workflow verified pause/resume, forged approval
rejection and exactly one fictional receipt after retry; its fixture was removed.
See [results](../../docs/RESULTS.md) and [deployment](../../docs/deploy-mcp.md).
A manually launched backend defaults to refund execution disabled; only the
reviewed internal Compose configuration opts in.

The remaining Day6 instructions describe the earlier direct-read development
mode. Host port8004 is optional historical development, not a current published
backend port or a requirement for the MCP-backed graph.

---

# Fictional mock backend — Day 6

This internal FastAPI service supplies synthetic customer/order/ticket facts for
the agent. It is not a commerce integration. Data lives in the local Postgres
database, separately from the hosted Knowledge API's policy corpus.

Implementation: `src/caseflow/mock_backend.py`, `mock_api.py` and the
composite tenant keys in `schema.sql`. Fixtures: `data/mock/entities.json`.
The optional direct development server can listen on loopback8004.

## Initialize locally

Use VS Code PowerShell in `G:\caseflow`, with Docker Desktop running.
Keep the existing `.env`; do not overwrite it. DATABASE_URL must point at the
local development database for these Day 6 commands (empty selects the default).

```powershell
cd G:\caseflow
docker compose up -d --wait db
uv run --frozen caseflow seed-mock
uv run --frozen caseflow provision-token --tenant northwind --scope kb:read --scope orders:read --scope tickets:read --scope agent:run --env-name NORTHWIND_AGENT_API_TOKEN
uv run --frozen caseflow provision-token --tenant contoso --scope kb:read --scope orders:read --scope tickets:read --scope agent:run --env-name CONTOSO_AGENT_API_TOKEN
```

The trusted seed command initializes the schema and inserts missing fixture rows
without replacing existing edits. Success reports 3 fixture customers, 5 orders
and 4 tickets. Prices use integer US cents. Dates and statuses are fixed fictional
examples; they are not a live clock or actual carrier information.

Token provisioning appends new values only to the ignored `.env`, prints metadata
only and stores hashes in local Postgres. It does not change the existing
Knowledge API tokens or register the new agent tokens in Neon. The agent uses
separate credentials for reading policy articles and reading the internal backend.

## Start when it is not already running

In a local PowerShell terminal at the project root:

```powershell
uv run --frozen uvicorn caseflow.mock_api:app --host 127.0.0.1 --port 8004 --no-access-log
```

Success: Uvicorn reports port 8004. Keep that terminal running; Ctrl+C stops this
foreground server. Check `http://127.0.0.1:8004/health` before starting a duplicate.
Interactive docs are at `http://127.0.0.1:8004/docs`; protected routes need an agent
token from the local .env. Never share token values or screenshot the Authorize field.

| Endpoint | Permission | Behavior |
|---|---|---|
| GET `/health` | Public | Process liveness |
| GET `/orders/{id}` | `orders:read` | Only the credential's tenant; foreign/missing ids both return generic 404 |
| GET `/tickets?limit=10` | `tickets:read` | Only open tickets in the credential's tenant; limit 1–50 |
| POST `/refunds` | Authenticated | Always 501: approval/execution workflow not enabled |

Tenant identity comes from the hashed token lookup, not query arguments. Unknown
query fields are rejected. Wrong scope is 403; expired/revoked credentials are 401.
Database failures have generic 503 responses. Request-id logs contain route, method,
status and duration, without prompts, credential values or returned order data.

The refund route is deliberately nonfunctional. `approved: true` supplied by a
model/caller cannot activate it. No refund ledger or durable approval queue exists
yet. Those belong to later PRD phases. The service stays local; no Docker/cloud
deployment is claimed for this Day 6 backend.

## Day 9 local ledger

The shared schema now includes agent_runs, refund_approvals and refunds. The local
durable CLI uses ApprovalStore for code-guarded, transactional fictional refunds
after a distinct operator decision. This HTTP service still returns 501 for
POST /refunds. Day 10 must expose the same boundary internally for deployment.
See [approval workflow](../../docs/approval-flow.md); no cloud schema was changed.
