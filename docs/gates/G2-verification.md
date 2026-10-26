# G2 verification: Day 10 release prepared, deployment pending

Date: 26 October 2026. This is evidence for technical checks, not an overall gate
pass or a passed learning assessment.

| Requirement | Evidence | State |
|---|---|---|
| Hosted at least 60% of 25 scenarios | 21/25 (84%) in paced Day 10 run; initial 14/25 preserved | Met for synthetic development evaluation |
| Local 25-case result recorded | qwen3:4b 22/25 (88%), same case/fixture hashes | Recorded |
| Refunds cannot execute without approval | Graph/API/ledger tests; unapproved HTTP resume/execution blocked | Verified in tested paths |
| Approval survives process restart | Independent processes with SQLite and Postgres checkpoints; one receipt after retry | Verified locally |
| Eight injection cases, no unauthorized action | Eight deterministic hostile-output/poisoned-data cases pass | Verified enforcement, not universal LLM immunity |
| Failed trace identifies failed step | Day 9 Langfuse read API verified ERROR intake/model_unavailable | API verified; manual screenshot pending |
| CI green for release | Local 308-test suite and all service image builds pass | Fresh remote CI pending user push |
| Services deployed and deployed flow verified | Local Docker HTTP workflow passes; EC2 SSH checked at old 531d7c4 | Pending release deployment and public smoke |
| Explain state/nodes/plain policy | User chose implementation first | Deferred, never passed |

Evidence lives in evals/results/day-10-*.json, day-09-failed-trace.json and
day-09-live-approved.json. Read [Day 10 results](../../evals/results/day-10-summary.md)
for fixture/scoring/model-setting changes; do not compare the percentages as an
intrinsic model ranking or claim a held-out benchmark.

The user must commit/push this reviewable release. Then verify CI, provision only
the configured Neon demo schema/role hashes, deploy on the existing EC2 instance,
and run the authenticated public HTTPS smoke before clearing deployment checks.
No new EC2 resources, paid services, model plan or broad IAM policy are required.
