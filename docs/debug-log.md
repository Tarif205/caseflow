# Debug log

One entry per non-trivial bug. Target: at least 15 by Day 14.

## 1 Docker build selected the wrong directory

Observed during setup sessions through 22 October 2026.
Symptom: Docker reported that Dockerfile did not exist, then could not find health-app.
Cause: the build used the repository root as its context; the Dockerfile was in
hello/health_app. The run error followed the failed build.
Fix: build from hello/health_app, then start the resulting image.
Verification: a running health-app container returned the expected /health response.
Check first next time: the working directory and the first failed operation.

## 2 Day 1 demo could overwrite the full corpus

Found during Day 2 code review on 22 October 2026, before the full corpus import.
Symptom: check-search wrote three short demo documents to the same tenant and ids
planned for the full help center. Rerunning it after ingestion would replace them.
Cause: experimental and application data shared storage identities.
Fix: give the experiment its own northwind-day1-demo tenant.
Verification: an integration regression test seeds a full Northwind article, runs
the demo, and asserts the full article is unchanged and the demo has its own rows.
No loss of user data is claimed. Check first next time: side effects of smoke-test
and seed commands, especially idempotent upserts sharing real application ids.

## 3 Neon pool rejected the query timeout startup option

Observed during hosted database initialization on 23 October 2026.
Symptom: init-db printed a generic database error even though application tables
had been created. A plain read-only Neon connection succeeded; the same connection
with startup options setting statement_timeout failed. No credential values were
printed during diagnosis.
Cause: migrate() connected without that option and committed the schema, then
bootstrap's second connection used an option rejected by the Neon pooler.
Fix: remove the startup option and execute SET LOCAL statement_timeout = '10s'
inside the connection's transaction before registering the vector adapter.
This keeps query protection and avoids leaking a setting to another pooled client.
Regression: a pooler-like startup rejection test against real local Postgres also
checks cancellation and recovery after a timed-out query in a savepoint.
Verification: 144 local tests passed; actual Neon bootstrap returned ready with
vector 0.8.6, two tenant rows, zero documents and SHOW statement_timeout = 10s.
The cloud image at revision 3d0bd84 predates this fix and must be rebuilt after
the user commits/pushes it. No commit/push performed by the assistant.
Reference: [Neon startup-parameter errors](https://neon.com/docs/connect/connection-errors#unsupported-startup-parameter).
Check first next time: whether the failing step is connection establishment,
schema creation or later initialization; poolers can reject otherwise valid
Postgres startup settings. Partial success across separate transactions is possible.

## 4 Native tool/final-output contracts failed in Day 6 model baselines

Observed 26 October 2026. Hosted GPT-OSS-20B completed four of five cases, but
s001 failed final parsing at step two after reading policy evidence. qwen3:4b
completed none: one model_unavailable around 62 seconds and four invalid model
outputs at step one before any tool execution. Evidence is saved in the Day 6
JSON artifacts; raw model reasoning/error bodies were deliberately not retained.

Response: retain the baseline failures rather than relaxing validation or choosing
only a successful rerun. The loop escalates safely and exposes no write tool.
Cause is bounded to provider/output-contract failures by the observed categories;
exact underlying native/text shapes and the first local availability cause are
not established. Local loading/unloading and tight memory/request budgets matter.
Future diagnosis should capture redacted finish/parse-stage metadata before
changing one setting, not assume all failures mean the model lacks tool support.
Unit tests verify invalid outputs/unknown tools/limits cannot become an action.
Local qwen3 was unloaded afterward. No unsafe fallback or refund path was enabled.

## 5 Langfuse read API returned serialized span output

Observed 26 October 2026 during Day 9 trace verification. Export succeeded and
the intake/root spans were visible through the read API, but the verification
assertion failed. Safe field-type inspection showed input=None and output=str.
The verifier assumed an already-decoded dictionary. Normalize JSON strings before
checking the allowed status/reason keys. Reverified delivered ERROR intake span
with model_unavailable. No raw response, model reasoning or credentials printed.
Check first next time: the returned field type; SDK serialization and API parsing
options can differ even when the underlying trace is correct.

## 6 A late deadline must not erase a committed write receipt

Found during Day 9 code review, before a demo refund was approved. The existing
read-only node guard replaced any late result with deadline escalation. Applied
unchanged to execute, it could conceal a committed mock refund. Preserve a
successful committed receipt after execution; still check deadline before starting.
Added a regression where the clock advances after execution and verified the
refunded result remains truthful. Ledger idempotency protects process-crash replay.
This was a reviewed risk and test fix, not an observed duplicate or demo refund.

## Template

```
### NN. Short title (Day N)
Symptom:
Hypothesis I wrote before changing anything:
Cause:
Fix:
What I would check first next time:
```
