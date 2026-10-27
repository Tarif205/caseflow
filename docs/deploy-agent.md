# Day 10 agent release and deployment

Current state: **deployed and verified**, release 47906e1b13eaf4f7318ad38e9777082b04ab5030.
Public base: https://16-178-30-70.sslip.io/agent. Release CI passed; public agent
smoke and the original Knowledge API smoke passed. Original Knowledge API remains
on 531d7c4. See [deployment evidence](../evals/results/day-10-ec2-deployment.json).
The sequence below documents the completed release and future repeat deployments.
User commits/pushes; the assistant does not commit.

## Service contract

The agent API authenticates every operational request. Bearer auth supplies tenant
and scopes; bodies cannot select identity, credentials, URLs or approval records.

| Route | Caller | Behavior |
|---|---|---|
| GET /health, /ready | Public | Liveness; Postgres checkpoint readiness |
| POST /runs | Worker, agent:run | Body ticket_id; identity bound to stored open ticket |
| GET /runs/{uuid} | Owning worker | Safe status, not raw checkpoint data |
| POST /runs/{uuid}/resume | Owning worker | No body; stored decision required |
| GET /approvals | Operator, refund:approve | Tenant-scoped pending proposals |
| POST /approvals/{uuid}/decision | Distinct operator | Strict boolean approved; immutable decision |

The internal backend's POST /refunds is opt-in via MOCK_REFUNDS_ENABLED=true.
Its body accepts **only run_id**. The backend derives amount/order from the ledger,
checks active worker and operator authority, policy and order snapshot, then
atomically records one mock refund. Caller approved=true or new amounts are rejected.
There is no public direct refund tool. Approver credentials never enter the model.

Postgres checkpoints replace SQLite in the API. Same-run advisory locks prevent
concurrent resume orchestration; refund row locks/constraints protect retries.
SQLite CLI remains supported for local study. Inputs are bounded to 4KiB and
logs contain route templates, request ids, status and duration, not bodies/headers.
Run ids are namespaced by tenant and checked against stored ownership before reads.

## Local containers already verified

PowerShell at G:\support-copilot, Docker Desktop running:

```powershell
$env:COPILOT_IMAGE_TAG='day10'
docker compose -f compose.yaml -f compose.agent.yaml run --rm --no-deps support-agent caseflow init-agent
docker compose -f compose.yaml -f compose.agent.yaml up -d mock-backend support-agent
.venv\Scripts\python.exe scripts/smoke_agent.py --base-url http://127.0.0.1:8002 --database local --output evals/results/day-10-local-container-smoke.json
```

Images must first be built with their service Dockerfiles or Compose --build.
The smoke uses a temporary synthetic tenant and simulated operator approval,
then removes its own rows/checkpoints. It never approves an existing demo request.
Both new containers are currently running locally; the earlier development stack
and manual backend terminal were preserved. qwen3 was stopped after evaluation.

## Release sequence after the user commits/pushes

1. Verify the new commit's GitHub checks, including both new Docker builds.
2. From local PowerShell, initialize the configured Neon demo and role hashes:

```powershell
.venv\Scripts\python.exe scripts/provision_agent_cloud.py
```

This explicit admin operation was performed for the deployed Day 10 release. It uses the
existing NEON_DATABASE_URL and local role tokens in memory; only hashes enter
Neon. It inserts missing fictional fixtures without overwriting existing rows.
No secret file is uploaded, no IAM expansion or new paid resource is needed.
Keep existing Knowledge API tokens intact. Schema changes are additive.

3. On the existing Ubuntu EC2 host, pull the user's release and run
   scripts/deploy_agent_ec2.sh with the **actual reviewed commit id** and current
   sslip.io hostname. The assistant can do this over the verified SSH connection
   after the commit exists; do not guess a future commit id.

The script builds the two tagged images on EC2, obtains the existing two Sydney
Parameter Store SecureStrings into exported variables, initializes checkpoints/
fixtures, and starts compose.agent-aws.yaml. It never prints expanded Compose
configuration or writes secret values to disk. Docker still retains runtime
environment in privileged container metadata; do not dump it.

4. After service readiness, the script changes Caddy to persist a config that
   routes `/agent/*` to loopback 8002 (prefix stripped) and preserves all other
   Knowledge API routes on loopback 8001. It keeps the old proxy container as
   support-copilot-proxy-before-agent, and reuses the certificate volumes.
   Backend has no published port; agent port 8002 remains loopback-only.

5. From local PowerShell, verify the real public HTTP flow on a temporary fixture:

```powershell
.venv\Scripts\python.exe scripts/smoke_agent.py --base-url https://16-178-30-70.sslip.io/agent --database neon --output evals/results/day-10-public-agent-smoke.json
```

Use the current verified hostname after an EC2 restart. This explicitly selects
Neon; it is not run against cloud by default. The test creates scoped synthetic
worker/operator tokens in memory, verifies pause/auth/approval/resume/idempotency,
then removes only its exact random tenant and checkpoint namespace. Its simulated
operator is not approval of a real or stored demo/customer request.

6. Recheck the existing Knowledge API /health and authenticated smoke, capture
   EC2 container memory, and update the G2 deployment/CI checklist from evidence.

## Rollback and operational limits

If the initial proxy replacement cannot start, the helper restores the original
proxy name and restarts it. For a later regression, stop the new agent services
without deleting data, stop/remove only the new proxy, rename
support-copilot-proxy-before-agent to support-copilot-proxy and start it. The old
Knowledge API image/container stays available. Do not remove certificate volumes,
Neon data or checkpoint tables as a rollback step.

Release CI and public proof are now verified in the saved Day 10 evidence. Deployment tracing is off unless existing Langfuse credentials are
provided securely; local Day 9 tracing is independently verified. The default
free-tier inference limits still apply. Do not upgrade plans to finish the gate.
No multi-worker load/DoS test or automatic approval-expiry policy is claimed.
