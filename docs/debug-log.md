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

## Template

```
### NN. Short title (Day N)
Symptom:
Hypothesis I wrote before changing anything:
Cause:
Fix:
What I would check first next time:
```
