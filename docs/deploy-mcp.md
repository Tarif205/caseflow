# Day 13 MCP deployment and local verification

Status on 27 October 2026: **approved and release-ready; awaiting user commit/push and CI**.
No Day 13 AWS service or public proxy route has been changed.

The user explicitly approved: "I approve exposing authenticated MCP on my existing
EC2 server and adding the two existing read-only MCP token hashes to Neon."
The approved source changes are now prepared and validated. This supersedes the
earlier approval-review rejections and general-instruction ambiguity. Do not ask
for the same approval again. The remaining prerequisite is the user-pushed release
and successful CI, followed by actual deployment and public checks.

- Expose authenticated HTTPS /mcp on existing EC2 i-073581e82c41622ea at the current
  documented hostname 16-178-30-70.sslip.io, with loopback-only upstream port8003.
- Store hashes of the existing NORTHWIND_MCP_API_TOKEN and CONTOSO_MCP_API_TOKEN
  in Neon with only kb:read, orders:read and tickets:read. Raw tokens remain private
  in local .env; no new SSM parameter, IAM policy or write/refund scope is needed.

Read-only EC2 preflight on 27 October confirmed checkout 47906e1, existing Day 10
agent/backend images, original Knowledge API, Caddy2.11.7, about 999 MiB available
RAM and the existing support-copilot-embeddings volume. No deployed state changed.

## Local result

Use PowerShell at G:\caseflow with Docker Desktop running and the existing local
database/corpus. The reviewed local configuration is compose.yaml plus
compose.agent.yaml. The current local services are already running.

```powershell
$env:COPILOT_IMAGE_TAG='day13'
docker compose -f compose.yaml -f compose.agent.yaml up -d --build --wait mcp-server mock-backend support-agent
.venv\Scripts\python.exe scripts/smoke_agent.py --base-url http://127.0.0.1:8002 --database local --require-mcp --output evals/results/day-13-local-agent-smoke.json
.venv\Scripts\python.exe scripts/check_mcp_http_inspector.py
```

The smoke uses only a random temporary tenant and simulated operator. It checks
the agent's configured read transport, actual MCP order lookup, approval pause,
unauthorized/foreign/forged operations, operator decision, resume and exactly one
mock refund after retry. Its own tenant/checkpoints are removed afterward. It
does not approve any existing demo/customer request.

The official Inspector 2.12.0 CLI runs with cached Node 24.22.1 and explicit legacy
protocol mode. The wrapper calls its installed runCli interface with a header
assembled in memory. The token is not in OS argv, a config file or the report.
This is a real Inspector HTTP check, not a browser screenshot. Its script accepts
--url, --token-env and --output for later public verification.

## Approved public change

Target the **existing** support-copilot EC2 instance i-073581e82c41622ea in Sydney
(ap-southeast-2), currently documented at https://16-178-30-70.sslip.io. Verify the
current instance IP and hostname before acting; they can change on stop/start.

1. After the user commits/pushes and fresh CI passes, build the reviewed CaseFlow
   MCP/agent/backend images on the existing host. CI now builds the MCP image too.
2. Add an MCP service to the existing support-copilot-agent Compose project, with
   a 512 MiB memory cap, bounded logs, non-root app user and loopback-only
   127.0.0.1:8003 mapping. Reuse the existing embedding cache volume and Neon
   DATABASE_URL from /support-copilot/DATABASE_URL through the current IAM role.
3. Add the exact public hostname, mcp-server, localhost and 127.0.0.1 to the MCP
   host allowlist. Keep explicit browser origins; non-browser clients omit Origin.
4. Point the updated agent's MCP_SERVER_URL to http://mcp-server:8000/mcp on the
   Docker network. Its same authenticated worker bearer supplies read authority.
   Keep refunds on the internal backend with the existing approval checks.
5. Add Caddy routing on the **existing HTTPS port 443**: exact /mcp forwards to
   127.0.0.1:8003/mcp; /mcp/health and /mcp/ready forward to the corresponding
   service health/readiness paths. Keep /agent/* and existing Knowledge API routes.
   Do not open port 8003 in the security group or bind it publicly.
6. Verify public MCP auth/tenant/resource/prompt behavior, official Inspector
   calls, the full agent workflow through /agent, the existing Knowledge API and
   EC2 memory. Save separate Day 13 public reports before marking G3 technical
   checks complete. The public agent smoke must use only its synthetic fixture.

Operational boundary: pre-provisioned bearer auth, not full OAuth discovery or
third-party consent. Exposing /mcp adds an authenticated public read endpoint and
an additional process sharing the existing database. There is no load/DoS claim.
No new instance, paid plan, IAM expansion, secret path, real payment integration
or seeded-user approval is part of this proposal.

## Release execution after the user pushes

1. Verify successful push CI for the exact full release SHA. The deployment helper
   independently checks the latest main/push run for that SHA and refuses missing,
   pending or failed CI before retrieving secrets or changing services.
2. Run the approved hash-only admin helper locally:

```powershell
.venv\Scripts\python.exe scripts/provision_mcp_cloud.py
```

   It uses only the configured NEON_DATABASE_URL and the two existing local MCP
   credentials. The operation is atomic/idempotent. It refuses to overwrite a
   scope mismatch or revive revoked/expired credentials. No raw value is printed
   or copied into a cloud file. Existing worker/operator credentials are unchanged.
3. On the verified EC2 host, update ~/support-copilot from the existing repository
   and verify its full HEAD matches the reviewed release SHA. Keep this checkout
   path because the existing proxy bind mount depends on it. Run:

```bash
bash scripts/deploy_mcp_ec2.sh FULL_REVIEWED_SHA CURRENT_IP_ENCODED_HOSTNAME
```

   The old deploy_agent_ec2.sh delegates to this helper. It checks clean/exact
   source, CI, existing proxy/cache volume and available memory before rollout.
   It builds MCP/agent/backend images, validates the Caddy candidate, waits for
   services, then reloads the existing proxy. It does not replace the Knowledge
   API or create a new instance, certificate volume, IAM role or SSM parameter.
4. Run the public checks from local PowerShell, using the verified current host:

```powershell
.venv\Scripts\python.exe scripts/check_mcp_http.py --url https://16-178-30-70.sslip.io/mcp --output evals/results/day-13-public-mcp.json
.venv\Scripts\python.exe scripts/check_mcp_http_inspector.py --url https://16-178-30-70.sslip.io/mcp --output evals/results/day-13-public-inspector.json
.venv\Scripts\python.exe scripts/smoke_agent.py --base-url https://16-178-30-70.sslip.io/agent --database neon --require-mcp --output evals/results/day-13-public-agent-smoke.json
.venv\Scripts\python.exe scripts/smoke_knowledge.py --base-url https://16-178-30-70.sslip.io --output evals/results/day-13-existing-knowledge-smoke.json
```

   The agent smoke creates and removes only its own temporary fixture identities,
   checkpoint namespace and fictional receipt. No seeded/customer request is approved.
   Capture actual EC2 container images/memory and CI metadata; update G3 from those
   results rather than assuming health checks prove the authenticated workflow.

## Approval history and rollback

Automatic approval review rejected the initial persistent AWS Compose/proxy patch
because a new public MCP endpoint broadens the production attack surface without
explicit approval for that target and scope. That patch was not applied. This
document records the reviewable proposal; it does not bypass the rejection.

Explicit approval subsequently authorized both listed changes. The cloud Compose
file now contains the private-port MCP service and the agent's fixed internal MCP
URL. New deploy_mcp_ec2.sh owns the approved release process; the old helper delegates.

The helper saves prior image references and proxy contents in an ignored
.cache/day13-rollback-RELEASE_PREFIX directory. On rollout failure it restores
those images/routes and stops a newly introduced MCP service. Proxy contents are
copied into its existing bind-mounted inode, so reload sees the intended file.
For an explicit rollback while checked out at the same release, run:

```bash
bash scripts/deploy_mcp_ec2.sh FULL_REVIEWED_SHA CURRENT_IP_ENCODED_HOSTNAME --rollback
```

Rollback preserves certificate volumes, Neon data/checkpoints and the original
Knowledge API. Approved read-only token hashes remain; rollback does not revoke
credentials. Recheck the Knowledge API and old agent workflow after rollback.

## Final local release checks

370 tests passed in 29.22s, including five new credential-provisioning cases.
scripts/check_mcp_deploy_safety.py passed in a network-disabled Linux container
with stubbed AWS/Docker/Git/curl commands: success, failed-CI refusal, failures
before/after proxy update, automatic rollback, explicit rollback and no credentials
in output. This is a dry run, not a claim of real EC2 failover testing.
scripts/check_mcp_deploy_config.py parsed Compose with dummy values and validated/
adapted the real Caddy template. All old routes and the private MCP mapping passed.
Both checks are now in CI. No real secret is needed for either configuration check.

## Memory snapshot, not capacity proof

Local Docker snapshot: MCP 264 MiB / 512 MiB; agent 113.1 / 384; backend 68.92 /
256; Knowledge API 78.2 / 768; Postgres 62.79 / 384. These are local observations,
not EC2 peak/load measurements. Recheck actual available memory after deployment.
