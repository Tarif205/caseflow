# Day 6 — mock backend and bounded agent loop

Date: 26 October 2026 (Asia/Dhaka). Assistant implementation under the explicit
implementation-first override. User learning checks remain deferred, never passed.

## What was built

- Local Postgres tables for customers/orders/tickets with composite tenant keys
  and tenant-aware customer foreign keys. No refund ledger or approval state yet.
- Validated fictional fixture set: 3 customers, 5 orders, 4 tickets. Idempotent
  seed inserts missing rows and preserves operator edits.
- Local internal FastAPI backend with GET /orders/{id}, GET /tickets and /health.
  Token hashes/scopes/expiry/revocation use the existing auth mechanism. Missing
  or malformed credentials fail before DB access; generic errors conceal foreign
  records and driver details. POST /refunds always returns 501, without execution.
- Two local agent credentials provisioned as new .env entries with kb:read,
  orders:read, tickets:read and agent:run. Hashes stored only in local DB. Existing
  Knowledge API tokens, hosted database and cloud services were not changed.
- Native Groq/Ollama tool-call adapter with provider-specific message conversion.
  Existing API JSON-answer adapter is unchanged. No new dependencies were needed.
- Plain agent loop with search_kb/get_order, strict arguments, bound principal,
  step/tool budgets, per-call timeout and call-boundary run-deadline checks.
- Final response code selects exact policy chunks or whitelisted order facts.
  It never returns unrestricted model prose or executes a proposed action.
  Refund proposals escalate to a human; no durable approval workflow is claimed.
- First 10 synthetic scenarios and an evaluation runner written before the real
  runs. Loop-vs-graph table records current behavior and future Day 8 plans.

## Verification and results

**196 tests passed in 12.66 seconds**, including real local Postgres tests and
fake-based model tests. Ruff lint and formatting passed. Tests cover native
provider wire differences, step/tool/deadline boundaries, missing evidence,
invented chunk ids, unavailable tools, injected tenant arguments, cross-tenant
reads, scope failures, expired/revoked tokens, preserved seed edits and a caller
attempting to enable refunds with approved=true. No refund executed.

Started the backend on laptop loopback 8004 and checked /health 200. Hosted/local
evaluations both used that real backend plus the deployed HTTPS Knowledge API.
All inputs were fictional. Native schemas were checked against current Groq and
Ollama documentation; installed versions include FastAPI 0.143.3, Pydantic 2.14.1,
httpx 0.28.1 and LangGraph 1.2.16 (not used by this plain loop).

| Provider/model | Cases | Successes | Observed failures |
|---|---:|---:|---|
| Groq openai/gpt-oss-20b | First five | 4/5 | s001 read policy evidence, then invalid final model output; escalated safely |
| Ollama qwen3:4b | Same five | 0/5 | s001 model_unavailable after 62.109s; s002–s005 invalid_model_output before any tool call |

Evidence: `evals/results/day-06-hosted.json` and `day-06-local.json`. Dataset hash
matches across runs; default bounds are 6 steps/6 calls/120s, with 60s maximum
per model request. The hosted 4/5 meets Day 6's minimum of 3/5. No optimization
rerun was selected to replace the baseline failures. The local unavailable result
does not retain raw HTTP status/body, so its exact underlying network/model-load
cause is not asserted. The invalid-output category means the native/JSON contract
was not satisfied; raw reasoning text was not retained or returned to a customer.

The laptop had approximately 852 MB free RAM before local testing. During testing
Ollama reported qwen3:4b 3.5 GB at 34% CPU/66% GPU and context 4096. The adapter
uses keep_alive=0, so local model loading/unloading overhead is part of this
configuration. These are configured application outcomes, not a controlled
comparison of intrinsic model capability. Stopped qwen3 after all five attempts;
ollama ps then showed no loaded models. No local model was left consuming VRAM.

## Limits and next step

Scenario labels are assistant-authored development fixtures, not independently
reviewed or held-out. Source/order field checks are not a semantic completeness
benchmark. The 25-case evaluation, full policy rules, graph, durable approvals,
trace instrumentation, injection suite, MCP and agent deployment remain future work.
The existing EC2 Knowledge API image remains 531d7c4 and was not replaced.

The loop's deadlines are checked around calls; HTTP timeouts do not provide an
OS-level preemptive kill for arbitrary code. Current requests are read-only.
Backend/runner remain local operator tools. Learning checks remain deferred.

Next PRD work is Day 7: complete 25 scenarios and implement/test the pure refund
policy (cap, eligibility/status, ownership and deny-wins). Approval/execution must
remain disabled until the later durable approval path is implemented and verified.
User commits/pushes. No assistant commit/push was made.
