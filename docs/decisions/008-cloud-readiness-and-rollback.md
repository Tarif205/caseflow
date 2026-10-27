# 008: cloud readiness budgets and rollback topology

Recorded: 28 October 2026. Incident and verification: 27 October 2026.
Status: accepted; deployed and publicly verified in release bb7491d.

## Evidence

Release 5bb883f passed CI but failed MCP readiness during EC2 rollout. The HTTP
probe allowed 3s. An existing agent readiness request took 4.18s against Neon;
the MCP probe logged TimeoutError while its Uvicorn startup was normal.
A private SSH-tunnel read then verified the MCP order tool and measured 24.73s
for initialization, notification, discovery/schema checks and the read. The
initial 20s client sequence budget was insufficient too.

Automatic rollback restored images and proxy contents but reused the new Compose
file. New health/dependency rules were inherited by the old images. Recovery
using the original 47906e1 Compose file restored the prior topology. Both the
public Knowledge API smoke and synthetic agent workflow smoke passed afterward.

## Decision

Allow 15s for DB-backed HTTP readiness, 20s for Docker's outer deadline and 30s
startup grace. Backend liveness remains short because it does not query Neon.
Allow 45s for an MCP read sequence, always clamped to remaining graph time.
Authority, tenant filters, approval requirements and finite budgets stay enforced.

Save the previous cloud Compose file from the running agent image's commit tag,
alongside previous image references and proxy contents. Rollback uses that prior
topology rather than merging old images into new health/dependency rules.
A stopped MCP container left by a failed attempt is not a running prior release.

## Verification and limits

370 tests passed with the CI pytest entrypoint. The Linux command-stub harness
checks previous-topology selection, stopped-orphan handling, automatic/manual
rollback and CI refusal. Real Compose/Caddy checks validate the probe margins.
The corrected release bb7491d passed CI40562465195 and deployed successfully.
Public SDK/Inspector, MCP-backed agent and original Knowledge smokes all passed.
See ../gates/G3-verification.md. Rollback regressions have harness coverage and
the first incident was recovered; no deliberate failover of this final release
was performed.
