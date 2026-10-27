# Gate G3: Day 13 evidence

Date: 28 October 2026 (Dhaka). **G3 technical checks passed.** Learner explanation
remains deferred/unassessed. Release `bb7491db816592e71f55b951ee77321429bb9155`
passed CI40562465195 and deployed on the existing EC2 host. Both public MCP tenant
clients, official Inspector CLI, MCP-backed synthetic approval workflow and the
original Knowledge API passed. The earlier5bb883f rollout incident was recovered;
its evidence remains below as history.

| Requirement | Evidence | State |
|---|---|---|
| Tools/resource/prompt tenant isolation and generic auth failures | Existing Day 11/12 tests plus new adapter and credential tests; 370 total tests passed | Local verified |
| MCP scenario rate no more than five points below direct result | Live MCP 22/25 (88%) vs archived direct 21/25 (84%); same dataset/immutable orders | Local verified, sampled development set |
| Transport comparison without model variability | 25/25 matches with direct-read replay of identical model decisions/input digests | Verified; replay control, not independent inference |
| Injection enforcement still passes | 8 surfaces x 2 adapters: 16/16 pass | Deterministic enforcement, not live-model immunity |
| Durable approval/refund through the MCP-backed agent | Public MCP-backed smoke: pause, auth failures, simulated operator, resume, one mock receipt, fixture cleanup | Public verified |
| Official Inspector against public deployment | Official Inspector2.12.0 CLI called all three public tools | Public verified |
| Public end-to-end smoke and existing-service regression | Two MCP tenant clients, agent workflow and original Knowledge API all passed | Public verified |
| Learner explanation without notes | No assessment performed | Deferred, never passed |

Evidence:

- [Technical gate summary](../../evals/results/day-13-g3-summary.json)
- [Corrected release CI](../../evals/results/day-13-corrected-release-ci.json)
- [Actual deployment and memory snapshot](../../evals/results/day-13-ec2-deployment.json)
- [Public SDK: tools, resource, prompt and isolation](../../evals/results/day-13-public-mcp.json)
- [Public official Inspector CLI](../../evals/results/day-13-public-inspector.json)
- [Public MCP-backed approval workflow](../../evals/results/day-13-public-agent-smoke.json)
- [Original Knowledge API regression](../../evals/results/day-13-existing-knowledge-smoke.json)

- [MCP live model run and replay comparison](../../evals/results/day-13-agent-mcp.json)
- [Injection report](../../evals/results/day-13-injections.json)
- [Local Docker workflow](../../evals/results/day-13-local-agent-smoke.json)
- [Official Inspector over HTTP](../../evals/results/day-13-local-inspector.json)
- [First release CI](../../evals/results/day-13-release-ci.json)
- [Rollback recovery](../../evals/results/day-13-rollback-recovery.json)
- [Restored agent workflow](../../evals/results/day-13-rollback-agent-smoke.json)
- [Restored Knowledge API](../../evals/results/day-13-rollback-knowledge-smoke.json)
- [Private cloud MCP latency](../../evals/results/day-13-cloud-read-latency.json)

The live run retried seven free-provider rate limits; all 25 scenarios completed.
Failures s001/s002/s012 were model escalation/missing evidence, not transport
differences. Original corpus and immutable order fixture hashes match the saved
Day 10 comparison. New random local tenants were removed afterward. No refund
was executed in the quality evaluation; approval there is a non-durable marker.
Only the separate synthetic smoke exercised a guarded mock refund.

370 tests passed in 30.10 seconds after the cloud timing correction, including the Postgres integration suite and
five new provisioning safety cases. Deployment rollback harness and real Compose/
Caddy configuration validation passed locally and are included in CI.
See [deployment guide and approval boundary](../deploy-mcp.md). Public technical
verification is complete; Day14 portfolio polish can follow the evidence commit.
The learner assessment remains deferred, never passed. The two-tenant SDK checker
needed180s overall rather than90s; this changes no production read/graph budget.
Memory is a single snapshot, not load evidence. No cloud trace export is claimed.
