# Day 13: MCP-backed agent, local proof and deployment boundary

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
