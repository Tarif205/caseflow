# Gate G3: Day 13 evidence

Date: 27 October 2026. **Local checks passed; public technical gate remains open.**

28 October update: CI40514197783 passed for5bb883f, but live rollout failed its
3s readiness deadline. Previous public services were fully recovered and both
original-service smokes passed. MCP remains stopped/unpublished. Corrected probe
and client time budgets plus prior-topology rollback await a new commit and CI.

| Requirement | Evidence | State |
|---|---|---|
| Tools/resource/prompt tenant isolation and generic auth failures | Existing Day 11/12 tests plus new adapter and credential tests; 370 total tests passed | Local verified |
| MCP scenario rate no more than five points below direct result | Live MCP 22/25 (88%) vs archived direct 21/25 (84%); same dataset/immutable orders | Local verified, sampled development set |
| Transport comparison without model variability | 25/25 matches with direct-read replay of identical model decisions/input digests | Verified; replay control, not independent inference |
| Injection enforcement still passes | 8 surfaces x 2 adapters: 16/16 pass | Deterministic enforcement, not live-model immunity |
| Durable approval/refund through the MCP-backed agent | Local Docker smoke: pause, auth failures, simulated operator, resume, one mock receipt, fixture cleanup | Local verified |
| Official Inspector against public deployment | Local HTTP Inspector verified; first rollout recovered, corrective commit/CI pending | Pending |
| Public end-to-end smoke and existing-service regression | Original services pass after recovery; public MCP-backed rollout still pending | Pending |
| Learner explanation without notes | No assessment performed | Deferred, never passed |

Evidence:

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
See [deployment proposal and approval boundary](../deploy-mcp.md). Do not mark G3
complete or start Day 14 release claims before public verification.
