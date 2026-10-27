# CaseFlow measured results

These are recorded development and smoke results, not production SLAs or independent
benchmarks. Original JSON reports are retained, including failures and recovery.

| Measurement | Recorded result | Source and qualification |
|---|---|---|
| Latest full automated suite | 370 passed, 30.10s | [Timing-fix record](../evals/results/day-13-cloud-timing-fix.json); local Postgres integration included |
| Help-center corpus | 18 articles, 36 chunks; 384-dimensional embeddings | [Ingestion](../evals/results/day-02-ingestion.json); 15 Northwind and 3 Contoso articles |
| Retrieval Recall@5 | 40/40 (1.000) | [Retrieval report](../evals/results/day-03-retrieval.md); in-sample synthetic questions |
| Retrieval baseline/larger-chunk MRR@5 | 0.950/1.000 | Same development set; operating 800/120 defaults were retained |
| Public Knowledge refusal | 10/10 negatives, zero HTTP errors | [API refusal check](../evals/results/day-05-public-refusals.json); does not establish general semantic correctness |
| Hosted direct agent | 21/25 (84%) | [Paced run](../evals/results/day-10-hosted-paced.json); earlier 429 failures are retained in the Day 10 summary |
| Local direct agent | 22/25 (88%) | [Local run](../evals/results/day-10-local.json); different provider/model, not controlled comparison |
| Hosted MCP-backed agent | 22/25 (88%) | [Live MCP run](../evals/results/day-13-agent-mcp.json); seven rate-limit retries recovered |
| Same-decision direct replay | 25/25 final-result matches | Same MCP report; replayed recorded decisions/input digests, not independent model inference or quality improvement |
| Injection enforcement | 16/16 across 8 surfaces and 2 adapters | [Report](../evals/results/day-13-injections.json); deterministic hostile outputs/data, not live-model immunity |
| Public MCP | Both tenants: 3 tools, resource, prompt; foreign reads masked | [SDK](../evals/results/day-13-public-mcp.json) and [official Inspector CLI](../evals/results/day-13-public-inspector.json) |
| Public approval and retry | Durable pause, forged resume blocked, one mock receipt, fixture cleanup | [Agent smoke](../evals/results/day-13-public-agent-smoke.json); simulated operator for temporary synthetic fixture only |
| Existing Knowledge after MCP deployment | Search/isolation/refusal/real cited answer passed | [Regression](../evals/results/day-13-existing-knowledge-smoke.json) |

The full agent quality scenarios use a non-durable approval placeholder and do not
execute refunds. The separate synthetic HTTP smoke exercises durable authority and
the actual internal mock backend. Do not interchange these two kinds of evidence.
The three MCP-quality failures s001/s002/s012 concern escalation/missing evidence.

## Deployment evidence

Current MCP/agent/backend application release: bb7491db816592e71f55b951ee77321429bb9155.
[CI40562465195](../evals/results/day-13-corrected-release-ci.json) passed before rollout.
Original Knowledge API531d7c4 and proxy/certificate volumes were preserved.
[Selected runtime metadata](../evals/results/day-13-ec2-deployment.json) confirms
loopback-only upstreams, non-root service users and an unpublished backend.

At one point during public smoke checks the host had 673.2MiB available; MCP used
272.7MiB, agent 121.3MiB, backend58.11MiB, proxy 19.92MiB and Knowledge 250.1MiB.
This is a snapshot, not peak memory, throughput or a concurrent-load benchmark.

The first CI-green rollout5bb883f failed a 3s readiness deadline and was recovered.
[Decision008](decisions/008-cloud-readiness-and-rollback.md) explains measured cloud
latency, bounded timing changes and restoring the previous Compose topology.
The final two-tenant SDK checker passed with 180s overall rather than 90s; production
read 45s/graph 120s limits did not change in that verification-only adjustment.

## Reproducibility

Follow the root README for local setup. Day 14 uses a fresh Git checkout, new
Docker volumes and isolated ports; [clean-clone report](../evals/results/day-14-clean-clone.json)
records actual outcome and elapsed time. Image build cache/tool installation are
reported separately from clean DB/model-cache state. Public verification requires
private pre-provisioned credentials; public status endpoints alone do not establish
that the authenticated workflow works.
