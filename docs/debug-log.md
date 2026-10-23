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

## Template

```
### NN. Short title (Day N)
Symptom:
Hypothesis I wrote before changing anything:
Cause:
Fix:
What I would check first next time:
```
