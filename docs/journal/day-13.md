# Day 13: MCP-backed agent, local proof and deployment boundary

## Day 13 public deployment verified on 28 October 2026

This supersedes the pending retry and recovered-only state below. Release
`bb7491db816592e71f55b951ee77321429bb9155` passed CI run 40562465195 and
was deployed successfully on the existing EC2 host. No assistant commit/push.

- Public authenticated MCP: https://16-178-30-70.sslip.io/mcp; agent at /agent.
  MCP/agent/backend images use bb7491db8165 and are healthy/non-root. MCP8003
  and agent8002 bind only loopback; backend has no published port. Original
  Knowledge531d7c4, proxy, certificates, data and checkpoints were preserved.
- Both real public SDK tenant clients passed three tools, article resource,
  prompt, missing auth and foreign/missing error parity; no session IDs issued.
  Official Inspector2.12.0 CLI called all three public tools successfully.
- Public MCP-backed agent synthetic smoke passed durable pause, tenant/scope/
  forged-resume rejection, simulated operator approval, resume and exactly one
  fictional receipt after retry. Temporary identities/checkpoints removed.
  Existing Knowledge smoke passed both tenants and a real cited model answer.
- The verifier's overall 90s two-tenant batch budget expired on its first run.
  Added bounded --timeout-seconds (5..300, default90), reran180s successfully.
  This verification-only change does not alter production45s read/120s graph limits.
- Snapshot: host673.2MiB available; MCP272.7MiB, agent121.3MiB, backend58.11MiB,
  proxy19.92MiB, Knowledge250.1MiB. This is not peak/load or SLA evidence.
- Evidence: day-13-corrected-release-ci.json, day-13-ec2-deployment.json,
  day-13-public-mcp.json, day-13-public-inspector.json,
  day-13-public-agent-smoke.json, day-13-existing-knowledge-smoke.json and
  day-13-g3-summary.json under evals/results. Earlier failure evidence retained.
- G3 TECHNICAL requirements verified; learner explanation deferred/unassessed.
  Historical live quality22/25 and replay parity25/25 retain their limitations.
  No cloud trace export, OAuth completeness or live-model injection immunity claim.
- NEXT: USER commits/pushes verification helper, docs and evidence. This evidence
  commit needs no runtime redeploy; application images remain bb7491db8165.
  Then Day14 portfolio polish/documentation/demo/CV. Approval persists; no new
  instance, paid plan, IAM resource or SSM parameter was created.


28 October continuation: release5bb883f passed CI and approved read-only hashes
were provisioned. Its rollout failed a3s readiness probe; cloud readiness measured
4.18s and private MCP discovery/read24.73s. Old public images/routes recovered;
full original agent and Knowledge smokes passed. MCP stopped, public route never
enabled. Source now uses15s/20s probe budgets,30s grace and45s read sequences,
restores previous Compose topology as well as images, and excludes stopped orphan
MCP containers from previous-release state. MCP now starts/checks before replacing
the current agent.370 tests and revised config/rollback checks pass. New user
commit/CI and successful public retry remain required. Approval persists.

Release-preparation update: explicit user approval now covers public MCP on the
existing EC2 host and two existing read-only token hashes in Neon. Prepared the
cloud Compose topology, atomic/idempotent hash helper, public MCP checker options
and CI-gated deploy/rollback script. 370 tests passed in29.22s. Mock-command Linux
rollback tests and actual Compose/Caddy validation passed; both added to CI.
No deployment or production credential mutation yet. Next is the user's release
commit/push and CI, followed by deployment and public G3 checks. Older approval
blocks and the initial365-test result below record the earlier local stage.

Date: 27 October 2026. Learning checks deferred.

Added MCPTools using locked SDK 1.30.0. Current HTTP workflow and durable CLI now
read through MCP; historical direct-loop tools remain for baseline comparison.
The adapter binds worker identity and endpoint outside model control, discovers
the fixed registry, validates schemas/outputs, rejects write tools, bounds the
whole request sequence and response size, and fails closed. Refund execution
remains on the internal backend with the authoritative approval ledger.

Added the non-root MCP Dockerfile and CI image build, plus the local Compose MCP
service on loopback 8003. Local agent/backend/MCP images tagged day13 built and
services passed health checks. Existing database volume and Knowledge API stayed
in place; Compose project support-copilot is intentionally preserved.

The live hosted 25-case MCP evaluation passed 22/25 (88%), versus saved direct
21/25 (84%). Seven rate-limit retries recovered. Each MCP result matched a direct
read replay with identical model decisions and input digests: 25/25 parity. This
isolates transport behavior but is not independent direct inference or proof of
quality improvement. Immutable fixtures were copied to random local namespaces
and removed afterward; the original refunded demo order was not reset.

All 365 tests passed in 29.80s. Eight hostile surfaces pass through both direct
and MCP adapters (16/16). A first targeted rerun hit Windows temp-directory ACL
errors; a dedicated temporary directory on G: resolved the environment issue.
Local Docker smoke then passed actual MCP reads, durable approval pause,
tenant/scope/forged approval denial, simulated operator decision, resume and
exactly one mock receipt on retry. Its exact synthetic namespace was removed.

Official Inspector 2.12.0 / isolated Node 24.22.1 listed/called all three tools over
local HTTP. Wrapper assembles the header in memory via the installed runCli export;
no token in OS arguments, config files or saved evidence. No UI screenshot claim.

Automatic approval review rejected the AWS Compose/proxy patch that would add a
new public MCP route. It was not applied or worked around. Existing EC2 routes
and services remain unchanged. Prepared a concrete deployment proposal in
docs/deploy-mcp.md; cloud Compose remains unchanged. The old deployment script
now fails safely until the reviewed MCP topology is present. G3 is open pending
explicit public-exposure approval, user release commit/push, fresh CI and public
Inspector/workflow/regression checks. No paid resources or new credentials added.
