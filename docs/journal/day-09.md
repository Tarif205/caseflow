# Day 9: persistence, human approval and tracing

Date: 26 October 2026. Implementation-first override; learning checks deferred.

Implemented a trusted local DurableAgent with SQLite checkpoints and LangGraph
interrupt/Command resume. Authenticated stored-ticket intake binds the customer;
model prose cannot supply identity. Postgres records run ownership, immutable
refund proposal, distinct human decision and idempotent mock refund receipt.

Added explicit CLI start/pending/approve/reject/resume commands. Worker and operator
are distinct scoped principals; existing read tokens were unchanged. New local
NORTHWIND_WORKER_API_TOKEN and NORTHWIND_APPROVER_API_TOKEN values were generated
only into ignored .env; only hashes entered local Postgres. No Neon/cloud schema
or deployment changes. HTTP POST /refunds remains disabled; the local command uses
the same repository boundary that Day 10 must expose internally for deployment.

Execution rechecks active scopes/expiry/revocation, tenant/run/customer/order,
cap and unchanged policy snapshot. Row locks and unique ledger constraints prevent
duplicate refunds; insert/order update share a transaction. Rejects cannot execute.
A committed receipt is preserved even if the active-call deadline passes afterward.
This demo closes the order after one refund, including partial amounts.

Verification: **291 tests passed in 16.87s**, with local Postgres integration,
separate-process restart, forged resume input, rejection/revocation/expiry/scope
loss, changed order/amount, wrong tenant and repeated execution. The isolated
restart check exited after the pause, simulated an operator in copilot_test and
resumed in a new process with model replay forbidden. Repeated resume left one
row. Random synthetic tenant removed afterward; no demo request auto-approved.

Metadata-only Langfuse spans wrap the run and nodes. Installed Langfuse 5.0.4,
SqliteSaver 3.1.2 and LangGraph 1.2.16 signatures checked against official docs.
Read API verified an ERROR intake span with model_unavailable from a deliberate
fake-model failure. Initial verifier wrongly treated JSON-string output as a dict;
corrected normalization and reverified. No raw prompts, reasoning, payloads or
credentials exported. Telemetry errors cannot prevent/replay operations.

Browser initialization failed with missing local kernel assets, so dashboard
screenshot is not captured. Delivery and failed node are API-verified; trace URL
and safe evidence saved in evals/results/day-09-failed-trace.json.

The real hosted run for NW-T002 reached a durable pause for a **$75 mock refund
of NW-1044**. Run 152af441-f371-43fd-9f01-b8626f8c9585 remains pending, with zero
Northwind demo refunds and the order still delivered. User must review and choose
approve/reject; the assistant has done neither. Evidence: day-09-live-pending.json.

See docs/approval-flow.md for exact commands, authority model and limitations.
No new dependencies or paid plan. Default loop/Day 8 runner still cannot execute
a refund. Day 10 remains next for diagnostics, both-model full evals, injection
suite, Postgres checkpointer, internal HTTP write boundary and deployment/G2.
The prior 56% model result does not meet G2's 60% target. User commits/pushes.

## User completed the human decision

The user ran the explicit approve command for the $75 NW-1044 proposal, then
resume --trace. The result reported refunded/approved_mock_refund with durable
approval. A read-only database query independently confirmed decision approved,
amount 7500, order refunded and exactly one receipt. Saved day-09-live-approved.json.
The earlier pending state above is historical evidence of the approval pause.
Next: user commit/push and CI, then Day 10.
