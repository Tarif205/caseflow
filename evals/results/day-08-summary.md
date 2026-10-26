# Day 8 hosted graph versus hand loop

Date: 26 October 2026. Model: Groq openai/gpt-oss-20b, existing free-tier account.
Dataset: 25 assistant-authored development cases, SHA-256
73106ad8730ce1bcf1688cc7c16ab836f0947d23ff53a7310b9bf4ae21c7b677.

| Engine | Full set | First five | Failures in full set |
|---|---:|---:|---|
| LangGraph | 14/25 (56%) | 5/5 | Nine model_unavailable; one policy_denied; one record_not_found |
| Hand loop | 10/25 (40%) | 4/5 | Six model_unavailable; seven refund_requires_human_workflow; one invalid output; one invalid evidence |

Artifacts: [graph](day-08-graph-hosted.json), [loop](day-08-loop-hosted.json).
All 50 results have refund_executed=false. Both complete runs are preserved;
there was no selection of a best retry run. Public policy reads used the existing
HTTPS Knowledge API; order reads used the real local backend on loopback 8004.
Both tenants' fixture credentials were used without expanding scopes.

The observed graph count exceeds the loop in this run and reproduces its first-five
behavior. It is **not** a controlled framework benchmark: model protocol changes
from native tool calls to structured intake/planning, runs are sequential, and six
steps means model turns for the loop versus node executions for the graph. Both
use six read attempts/120s boundary budgets and at most 60s per model request.
These run files predate the explicit step_unit metadata added to future reports.

## What the failures mean

- Graph s006 correctly denies a refund because the real demo principal lacks
  refunds:propose and no trusted end-customer identity was supplied. Its label
  expects approval under a verified synthetic context, so it fails completion.
  Tests prove that verified, scoped synthetic contexts reach the non-durable
  approval placeholder; live credentials were not widened to improve a score.
- Graph s023 correctly stops at a tenant-bound foreign-order 404. The Day 7
  fixture label requires downstream policy mismatch reasons, so this strict
  completion judge marks it false. This exposes a fixture/runtime expectation
  mismatch: pure policy defense-in-depth tests can supply a foreign order, while
  a secure runtime lookup must never return it. The label was not changed during
  or after the run to inflate the measurement.
- Graph s016-s022 and s024-s025 returned model_unavailable. Earlier adapters
  conceal raw provider bodies/status on this path; their individual causes are
  not established. The loop also had six model_unavailable outcomes. Do not
  assert that all are timeouts, quota errors or a persistent provider outage.
- A separate safe status probe with max_tokens=20 returned HTTP 400; a normal
  max_tokens=600 probe returned HTTP 200. No raw response or reasoning retained.
  These probes do not diagnose the individual failed scenario requests.
- The loop has no code policy or approval marker, so safe refund escalations do
  not satisfy the newer code-policy/approval expectations. Its s005 was invalid
  final output and s012 selected invalid evidence.

No live approval success, refund execution, durable pause/resume or held-out
semantic success is claimed. Placeholder-aware scoring is explicitly opt-in and
does not count as durable approval verification. Gate G2 (Day 10) is still open;
56% is below its full-scenario 60% target. Improve diagnostics, reconcile the
foreign-order expectation and verify real approved workflow before that gate.

## Automated verification

**266 tests passed in 7.42s**, including local Postgres integration tests. Tests
cover every graph branch, missing scope/identity, foreign-order failure, injected
intake fields, forged evidence, node/tool/deadline limits, failed-read counting,
JSON transport/timeout behavior and independently disabled execute. Prior policy
tests retain the 1,260-combination finite-domain deny-wins check.

Local qwen3 was not rerun for Day 8; its Day 6 0/5 remains recorded. Both-model
full evaluations are scheduled for Day 10. No new dependencies, paid plan,
cloud deployment, credentials or schema changes were introduced.
