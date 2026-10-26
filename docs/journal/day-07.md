# Day 7: scenarios and deterministic refund policy

Date: 26 October 2026 (Asia/Dhaka). Implementation-first override active; learning
checks and Academy study deferred, never marked passed.

Completed Day 7 implementation requirements:

- Expanded ten scenarios to 25, both tenants and reply/escalation/denial/approval.
- Preserved the original dataset byte for byte in scenarios-day06.jsonl; tests
  verify its hash against both saved Day 6 model reports.
- Added pure policy: $80 cap, positive integer USD cents, order-total bound,
  delivered status, tenant/customer/order match, scopes and deny-wins precedence.
- Eligible refunds return needs_approval with execution disabled. No approval
  flag or broader scope can override a denial. Existing tokens gained no scope.
- Documented scenario format and cap decision. Runner supports dataset selection
  and up to 25 cases; generic escalation cannot satisfy policy/approval checks.

Verification: **245 tests passed in 6.92 seconds**, including local Postgres tests.
More than 15 policy cases cover every denial, exact boundaries, missing/foreign/
wrong-owner orders, non-USD, statuses, unknown approval fields and immutable inputs.
A finite exhaustive check covers **1,260 combinations** of amount, tenant/customer,
status, scopes and currency. Ten policy scenarios match fictional order fixtures.

This verifies eligibility, not deployed approval safety. The loop still escalates
all refunds and POST /refunds remains disabled. The policy is independent until
Day 8 integrates it with trusted intake and graph state. No model calls, cloud
deployments, schema changes, new credentials or dependencies for Day 7. Day 6's
hosted 4/5 and local 0/5 remain the latest model results; no 25-case rate claimed.

Next: Day 8 LangGraph rebuild, code policy and a non-executing approval placeholder.
Durable human approval/restart-resume belongs to Day 9. User commits/pushes pending
Day 6/7 changes; assistant made no commit/push.
