# 004: Code-enforced refund eligibility and an $80 demo cap

Date: 26 October 2026. Status: pure function implemented; graph integration and
durable human approval remain future work.

## Decision

`src/support_copilot/policy.py` evaluates proposed actions against trusted identity,
scopes and an order. It has no model calls, database access, clock, network or writes.
A model can propose; code restricts that proposal.

The fixed demo cap is **8,000 integer USD cents ($80)**, matching the PRD's sample
configuration. This is an invented business rule, not a legal requirement or a
statement about help-center return eligibility.

An eligible refund needs all of these:

- Actor has `agent:run` and explicit `refunds:propose` scope.
- Trusted intake supplies customer identity; order tenant/customer/id match.
- Stored order is delivered, currency USD.
- Amount is a positive integer number of cents, at most $80 and the order total.
  Floats, strings and booleans are rejected by validation.
- No earlier restriction denied the action.

Every failed condition contributes a reason. A prior denial blocks every action;
adding scopes cannot override it. Unknown fields/actions/statuses fail validation.
Callers must treat validation failures as denial/escalation, never permission.

Outcomes are reply, escalate, denied and needs_approval. **Every outcome has
execution_allowed=false.** Eligibility is not approval. There is no approved=true
input and no execution capability. The loop and backend still cannot execute a
refund. No approval is queued, persisted or approved by adding this function.

## Alternatives and consequences

| Option | Benefit | Cost or risk |
|---|---|---|
| Model enforces the cap | Little code | Cannot enforce identity, money or approval |
| Configurable cap and broad eligibility | Flexible | Easier to widen permissions; unclear fictional rules |
| Fixed cap, delivered-only, code checks | Deterministic and testable | Conservative denial of shipped/processing orders and non-USD |

We chose the third option. No calendar window or proof of damage is inferred:
fixtures lack delivery dates/evidence. A human must review the reason and article.
There is no refund ledger, so aggregate partial refunds/concurrent duplicates are
not prevented here. Eventual execution needs transactional ledger/idempotency checks.

## Trust boundary and verification

Customer identity must come from verified ticket/customer binding, not ticket
assertions. Orders must come from tenant-bound storage. Day 6 CLI establishes no
end-customer session and remains read-only. Existing tokens were not granted
refunds:propose. No schema, cloud deployment, new credentials or dependencies needed.

Tests cover every denial, exact cap/order-total boundaries, input validation and
accumulated reasons. A finite exhaustive property check covers 1,260 combinations,
checking eligibility predicates and prior-denial precedence. This is not proof
for all Python values or deployed approval safety.

Revisit when fictional rules add delivery dates, other currencies or a ledger.
Require new tests/scenario labels; never let the model choose the cap or identity.
