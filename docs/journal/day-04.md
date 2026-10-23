# Day 4 technical record

Date: 22 October 2026. Assistant implementation under the user's override.
Learning checks remain deferred. No commit, push or public deployment was performed.

## Implemented

- FastAPI health/readiness, scoped search/ask/ingest routes, validated bodies and
  a 256,000-byte request limit. Tenant identity comes exclusively from the token.
- Hashed bearer credentials, scope checks, expiry/revocation checks and safe local
  provisioning into the existing ignored `.env`. No credential values were printed.
- Ollama and compatible hosted JSON adapters, with timeouts and safe error handling.
- Extractive answers: the model selects chunk ids and quotations; code verifies
  original source membership and returns canonical source text with citations.
  Below-threshold evidence and concrete order references do not call the model.
- Request-id JSON logs, non-root multistage Docker image, Compose service and
  empty-only corpus initialization. Existing corpus/API edits survive restarts.
- GitHub Actions workflow for lint, formatting, Postgres tests and image build.
  The workflow has not yet run on GitHub.

## Verified

- 143 tests passed, including real Postgres integration, cross-tenant model context,
  idempotent ingestion, insufficient/expired/revoked tokens, fabricated quotes,
  malformed outputs, oversized bodies and safe database/provider failures.
- Ruff lint and formatting passed. Docker image built and service became healthy.
- Actual Docker request path: HTTP client -> bearer authentication -> Postgres ->
  CPU FastEmbed -> tenant retrieval -> Groq `openai/gpt-oss-20b` -> verified quote.
- Live smoke returned the original one-year manufacturing-defect warranty quote,
  citing `warranty.md`. `/health` and `/ready` returned 200; missing token returned
  401; both tenants' search results matched their own source files; an exact
  refund approval-date question was refused with `record_lookup_required`.
- Saved evidence: `evals/results/day-04-api-smoke.json` and
  `evals/results/day-04-api-transport.json`; runner: `scripts/smoke_knowledge.py`.
- Used hosted inference because host free RAM was approximately 0.5 GB. No local
  heavy model was loaded. The Groq key was already present; a small real generation
  succeeded with that account. Model availability is account-specific.

## Decisions and limitations

Keep baseline 800/120 chunks and the provisional baseline similarity threshold
0.691243. The larger-chunk retrieval win did not establish better answer/refusal
behavior. Quote validation establishes provenance, not semantic completeness or
immunity to prompt injection. One successful real answer is not a quality benchmark.
See `docs/decisions/002-grounded-answers.md`.

The current container was started with temporary PowerShell hosted-model overrides;
the existing `.env` still defaults to Ollama. Recreating it from another terminal
requires the commands in `services/knowledge-api/README.md`. API tokens remain in
the ignored `.env`; only hashes are stored in the local database. The public demo
database password is for loopback development only. No RLS, public TLS or rate
limiting is claimed. Readiness checks embeddings/database, not live model quota.

## Next step

Day 5 deployment preparation: verify current zero-cost hosting terms, establish
an available account, configure hosted database/model and secrets, then deploy and
run the same smoke check over HTTPS. Do not provision paid resources. The PRD
prefers AWS and allows a free fallback if signup/card requirements block it.
No sprint gate is claimed complete until its outstanding requirements are verified.
