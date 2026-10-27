# CaseFlow

CaseFlow is a support automation portfolio project for fictional Northwind Outfitters
and Contoso. It retrieves cited policy evidence, reads order facts through MCP,
and pauses a LangGraph workflow for a separate operator before recording a mock refund.
All customer data and payments are fictional.

**Deployed:** MCP/agent/backend release `bb7491d`, with the original Knowledge API
`531d7c4`, on the existing AWS EC2 server. Public verification passed on 28 October
2026 (Dhaka). Authenticated endpoints require private scoped tokens.
[Public health](https://16-178-30-70.sslip.io/health) is available while that instance
is running at the recorded IP. [Deployment evidence](docs/gates/G3-verification.md).

| Measured result | Scope and evidence |
|---|---|
| 370 automated tests passed | Includes local Postgres integration; [release record](evals/results/day-13-cloud-timing-fix.json) |
| Agent: 22/25 scenarios (88%) | Live hosted MCP run on synthetic development cases; [results](evals/results/day-13-agent-mcp.json) |
| Retrieval Recall@5: 1.000 on 40 questions | In-sample, assistant-authored labels; [methodology](evals/retrieval/README.md) |
| 16/16 injection enforcement checks | Eight surfaces through two adapters; deterministic checks, not model immunity |
| Public approval and retry checks passed | One mock receipt after repeated resume; temporary smoke fixture removed |

[Full results and limitations](docs/RESULTS.md) ? [Architecture](docs/architecture.md) ?
[Demo guide](docs/DEMO.md) ? [Portfolio and CV material](docs/PORTFOLIO.md)

## How the services work together

```mermaid
flowchart LR
    W[Worker] --> A[Support Agent / LangGraph]
    A -->|Scoped read calls| M[Read-only MCP]
    M --> D[(Postgres / pgvector)]
    K[Knowledge API] --> D
    O[Separate operator] -->|Stored approval| A
    A -->|Approved run ID| B[Internal mock backend]
    B -->|Policy, authority, one receipt| D
```

| Component | Responsibility | Local address |
|---|---|---|
| [Knowledge API](services/knowledge-api/README.md) | Ingest, retrieve, select validated quotations with citations | http://127.0.0.1:8001/docs |
| [Support Agent](services/support-agent/README.md) | Read evidence, plan, check policy, pause/resume with durable approval | http://127.0.0.1:8002/docs |
| [MCP server](services/mcp-server/README.md) | Three read tools, article resource, draft prompt; fresh bearer auth | http://127.0.0.1:8003/mcp |
| [Mock backend](services/mock-backend/README.md) | Fictional order/ticket storage and guarded mock refund endpoint | Docker network only |

Python 3.12, FastAPI, LangGraph, official MCP Python SDK, FastEmbed/BGE-small
(384 dimensions), Postgres/pgvector, Docker Compose, GitHub Actions, AWS EC2,
SSM Parameter Store and Neon. Chat adapters support Ollama and compatible hosted
inference; the recorded hosted runs used Groq. Dependency versions are in `uv.lock`.
Langfuse metadata traces were verified locally; deployed trace export is not claimed.

## Fresh local setup: policy search without a chat key

Prerequisites: Git, Docker Desktop running Linux containers, `uv`, Python 3.12
(uv can provision Python), free ports 5432/8001/8002/8003. Use PowerShell 5.1.
Image/package/model downloads need network access. First startup may take several
minutes; the recorded warm-build time is not a promise for a new machine.

In a new parent directory, clone and open the project:

```powershell
git clone https://github.com/Tarif205/caseflow.git
cd caseflow
uv sync --frozen
```

For an existing checkout, enter its folder instead of cloning again. Preserve an
existing `.env`. With a fresh checkout, no `.env` is required for the search-only
setup below. Local `DATABASE_URL` must be empty/unset or the default loopback DB;
`NEON_DATABASE_URL` is never selected automatically for local commands.

```powershell
docker compose up -d --wait db
uv run --frozen caseflow init-agent
uv run --frozen caseflow seed-mock
uv run --frozen caseflow provision-token --tenant northwind --scope kb:read --scope kb:write --env-name NORTHWIND_API_TOKEN
uv run --frozen caseflow provision-token --tenant contoso --scope kb:read --env-name CONTOSO_API_TOKEN
docker compose up -d --build --wait --wait-timeout 300 knowledge-api
uv run --frozen python scripts/smoke_knowledge.py --skip-model
```

Success: healthy Knowledge API, both tenant searches isolated, missing bearer401,
and refusal of a concrete order question; `live_model_tested` is false. Tokens
are generated into ignored `.env` and only hashes are stored in the local database.
The public demo DB credentials in Compose are local-only and bind loopback5432.
Startup seeds18 documents/36 chunks; no LLM server is required for this check.

## Add MCP and the agent

```powershell
uv run --frozen caseflow provision-token --tenant northwind --scope kb:read --scope orders:read --scope tickets:read --env-name NORTHWIND_MCP_API_TOKEN
uv run --frozen caseflow provision-token --tenant contoso --scope kb:read --scope orders:read --scope tickets:read --env-name CONTOSO_MCP_API_TOKEN
docker compose -f compose.yaml -f compose.agent.yaml up -d --build --wait --wait-timeout 300
uv run --frozen python scripts/check_mcp_http.py --timeout-seconds 180 --output .cache/local-mcp-check.json
```

Success: two tenant clients call all three tools, read their own article at the
same URI and prepare the prompt. The prompt itself calls no model or action.
Agent readiness at http://127.0.0.1:8002/ready reports `read_transport: mcp`.
The backend has no published host port. Compose retains the old project/volume
names intentionally; see the [rename compatibility map](docs/rename-caseflow.md).

To run real agent planning, add your own compatible hosted key as `LLM_API_KEY`
in ignored `.env`, then recreate the agent with the same Compose command.
`compose.agent.yaml` selects the recorded Groq-compatible endpoint/model; provider
access and quotas are external prerequisites. No key is shipped in this repository.

The following opt-in smoke creates its own temporary fictional customer, worker
and operator, simulates that fixture's approval, verifies one mock receipt after
retry, then removes its fixture/checkpoints. It never approves an existing request:

```powershell
uv run --frozen python scripts/smoke_agent.py --base-url http://127.0.0.1:8002 --database local --require-mcp --output .cache/local-agent-smoke.json
```

For manual role-separated approval and a recording, follow [the demo guide](docs/DEMO.md).
For a generated Knowledge answer, see its service README's provider settings;
`/ready` does not check live chat quota. Local setup makes no AWS or Neon changes.

## Tests and CI

```powershell
uv run --frozen ruff check src tests scripts evals/retrieval
uv run --frozen ruff format --check src tests scripts evals/retrieval
uv run --frozen pytest -q -m "not integration"
```

For the full suite, start the local DB and create a separate test database once:

```powershell
docker compose exec -T db createdb -U copilot copilot_test
$env:TEST_DATABASE_URL = 'postgresql://copilot:copilot-local-only@127.0.0.1:5432/copilot_test'
uv run --frozen pytest -q
```

If that database already exists, skip `createdb`. Integration tests reject remote
DBs and other database names; without `TEST_DATABASE_URL`, they skip explicitly.
CI runs lint, formatting, all tests, deployment rollback/configuration checks and
four image builds. It is **continuous integration**, with a separately invoked,
CI-gated deployment helper; pushes do not automatically deploy to EC2.

## Operations and boundaries

Stop local services while preserving data:

```powershell
docker compose -f compose.yaml -f compose.agent.yaml stop
```

Tenant identity/scopes come from a hashed bearer credential, never model arguments.
Refund policy, current order facts, separate durable approval and transactional
idempotency are enforced in code. MCP cannot approve or execute refunds.
Tenant SQL filters/composite foreign keys are used; PostgreSQL RLS is not implemented.
This project bearer scheme is not a complete MCP OAuth authorization server.

The model can still misunderstand evidence or escalate unnecessarily. Development
metrics are not held-out production quality, and cited quotations do not guarantee
semantic completeness. No load/availability guarantee or real payment integration
is claimed. See the [threat boundaries](docs/mcp-threats.md).

## Documentation and next steps

- [Results and evidence](docs/RESULTS.md), [G3 technical verification](docs/gates/G3-verification.md), [G4 checklist](docs/gates/G4-verification.md)
- [AWS Knowledge deployment](docs/deploy-aws.md), [current MCP/agent deployment and rollback](docs/deploy-mcp.md)
- [Eight architecture decisions](docs/decisions/README.md), [approval flow](docs/approval-flow.md)
- [Project explained from zero](docs/PROJECT_EXPLAINED.md), [learning roadmap](docs/LEARNING_ROADMAP.md)
- [Demo recording guide](docs/DEMO.md), [CV and walkthrough material](docs/PORTFOLIO.md)

Day 14 documentation and reproducibility checks are in progress. Recording and
learner walkthrough remain pending; learning checks are deferred, never passed.
Historical journal and evidence retain the original project name and earlier states.
