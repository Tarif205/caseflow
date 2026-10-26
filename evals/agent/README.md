# Agent development scenarios

`scenarios.jsonl` is the Day 7 **25-case** synthetic development dataset. It covers
policy replies, order status, missing/foreign records, refund denials and eligible
refund requests needing human approval. Both Northwind and Contoso are covered.
Labels are assistant-authored, not held-out or independently reviewed.

## Format

One JSON object per line, validated by `Scenario` in `agent_evaluation.py`:

| Field | Meaning |
|---|---|
| `id`, `tenant`, `ticket` | Unique s### id, fixture tenant and untrusted input text |
| `expected_action` | reply, escalate or refund (a proposal needing approval) |
| `expected_doc` | Required citation article id, or null |
| `expected_order`, `expected_status` | Expected fixture order/status, or null |
| `needs_approval` | True for eligible refunds; never optional on refund labels |
| `customer_id` | Trusted synthetic intake identity, not identity from ticket prose |
| `proposed_amount_cents` | Proposed integer cents for deterministic policy cases |
| `expected_amount_max_cents` | Maximum for eligible refund proposal |
| `expected_policy_reasons` | Required code-denial reason names; default empty |
| `injection` | Hostile instruction case; default false |

The first five retain Day 6 tickets and expected evidence. Ten refund cases have
deterministic policy inputs: two require approval and eight are denied. Tests use
`data/mock/entities.json`, without models or writes. The foreign-order policy test
deliberately supplies a foreign fixture for defense in depth; runtime reads must
already enforce tenant isolation.

## Versioned baseline

`scenarios-day06.jsonl` preserves the original ten cases byte for byte; its hash
matches both saved Day 6 reports. In that dataset s006 expected escalation. In
Day 7 it expects an eligible proposal needing approval. Do not relabel old results.
Hosted passed 4/5; local passed 0/5. See [Day 6 results](../results/day-06-summary.md).
These measurements do not establish success on the expanded dataset.

## Current evaluation limits

The runner remains the read-only loop. Reply checks require source substrings from
the right tenant and expected article/order/status. Infrastructure failures cannot
count as successful escalation. Policy-denial cases additionally require
reason=policy_denied and the expected code reasons; generic escalation is
insufficient. Approval cases fail the default judge because the loop cannot produce durable
approval state. Day 8 graph runs explicitly opt into non-durable placeholder
checks (state=required, matching order/amount, no execution, eligible code policy).
That mode is labeled in results and does not verify Day 9 durable approval.

Runner `--count` supports 1 through 25, default five. `--scenarios` selects a
dataset. To repeat the original-sized run, in PowerShell at G:\support-copilot
with the mock backend running:

```powershell
.venv\Scripts\python.exe scripts/run_agent.py --provider hosted --evaluate --count 5 --scenarios evals/agent/scenarios-day06.jsonl --knowledge-url https://16-178-30-70.sslip.io --output evals/results/day-06-hosted-rerun.json
```

This performs a new provider run, not identical output. Day 7 did not perform
another model run. Results record dataset hash, provider/model, limits, selected
facts and failures, without raw reasoning, credentials or upstream error bodies.
Source membership does not judge semantic completeness. Two marked injection
cases are not Day 10's full eight-case suite. Preserve failures and all results;
do not publish only the best retuned run.

## Day 10 evaluation version

The Day 7/8 25-case dataset is preserved byte-for-byte in scenarios-day07.jsonl.
Current s023 additionally allows expected_terminal_reasons=[record_not_found]: a
secure foreign-order read must stop before policy sees the foreign row. The pure
policy mismatch expectations remain for defense-in-depth tests. This change was
made before new runs, not used to relabel old results.

scripts/evaluate_agent.py uses immutable fictional orders and actual KB retrieval,
with trusted synthetic identity/scope inputs that never enter model permissions.
Both full model runs and the initial rate-limited run are preserved in
[Day 10 results](../results/day-10-summary.md). Quality evaluation counts an
explicit non-durable approval-required marker; Postgres/HTTP authorization and
restart are independently tested. No quality run executes a refund.

injections.jsonl contains eight hostile-surface fixtures. scripts/check_injections.py
runs deterministic adverse-model/poisoned-data tests, not empirical live-model
prompt immunity. Every case must end without unauthorized execution.
