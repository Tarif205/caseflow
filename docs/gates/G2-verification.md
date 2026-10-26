# G2 verification: technical checks verified for deployed Day 10 release

Date: 26 October 2026. Technical release checks are verified. Learning
checks remain deferred, never passed; no independent understanding is claimed.

| Requirement | Evidence | State |
|---|---|---|
| Hosted at least 60% of 25 scenarios | 21/25 (84%) in paced Day 10 run; initial 14/25 preserved | Met for synthetic development evaluation |
| Local 25-case result recorded | qwen3:4b 22/25 (88%), same case/fixture hashes | Recorded |
| Refunds cannot execute without approval | Graph/API/ledger tests; unapproved HTTP resume/execution blocked | Verified in tested paths |
| Approval survives process restart | Independent processes with SQLite and Postgres checkpoints; one receipt after retry | Verified locally |
| Eight injection cases, no unauthorized action | Eight deterministic hostile-output/poisoned-data cases pass | Verified enforcement, not universal LLM immunity |
| Failed trace identifies failed step | Day 9 Langfuse read API verified ERROR intake/model_unavailable | API verified; manual screenshot pending |
| CI green for release | Release 47906e1, Actions run 40340314622 completed successfully | Verified remote CI |
| Services deployed and deployed flow verified | EC2 agent/backend 47906e1; public HTTPS approval flow and original Knowledge API smoke pass | Verified deployed flow |
| Explain state/nodes/plain policy | User chose implementation first | Deferred, never passed |

Evidence lives in evals/results/day-10-*.json, day-09-failed-trace.json and
day-09-live-approved.json. Read [Day 10 results](../../evals/results/day-10-summary.md)
for fixture/scoring/model-setting changes; do not compare the percentages as an
intrinsic model ranking or claim a held-out benchmark.

Release 47906e1b13eaf4f7318ad38e9777082b04ab5030 was pushed by the user and
[passed CI](https://github.com/Tarif205/support-copilot/actions/runs/40340314622).
It is deployed at https://16-178-30-70.sslip.io/agent. Public smoke verified auth,
isolation, durable pause, simulated operator decision and exactly one receipt after
retry, then removed the synthetic tenant/checkpoints. No real/demo request approved.
The existing 531d7c4 Knowledge API passed its complete authenticated smoke afterward.

Evidence: day-10-release-ci.json, day-10-ec2-deployment.json,
day-10-public-agent-smoke.json and day-10-existing-knowledge-smoke.json under
evals/results. Existing EC2 reused, no new paid service or IAM expansion.

The manual trace screenshot and learner explain-back remain deferred. Local trace
delivery is API-verified; deployed agent tracing is off until credentials are
provided securely. Do not claim deployed trace export or learning mastery.
Next PRD technical work: Day 11, read-only MCP fundamentals/server.
