# Day 10 model and security verification

Date: 26 October 2026. All scenarios are assistant-authored development fixtures;
they are not held-out or independently reviewed.

| Run | Success | Observed failures |
|---|---:|---|
| Hosted initial, 3s case spacing | 14/25 (56%) | Eight confirmed HTTP 429 rate-limit failures; three over-escalations |
| Hosted paced, 12s case spacing | **21/25 (84%)** | Four over-escalations; zero rate-limit retries used |
| Local qwen3:4b, 3s case spacing | **22/25 (88%)** | Two invalid-evidence selections; one over-escalation |

Full reports: [initial hosted](day-10-hosted.json), [paced hosted](day-10-hosted-paced.json),
[local](day-10-local.json). All complete, all 25 rows retained, no refund writes.
The initial run was not replaced or relabeled. Pacing addressed measured HTTP 429
responses, rather than assuming that every model_unavailable meant a timeout.

## Configuration and interpretation

The new runner uses immutable original fictional order fixtures, so the user's
completed Day 9 refund does not change the benchmark. Knowledge retrieval uses
the real deployed API and existing tenant KB credentials. Fixture identities and
proposal scopes are explicit trusted test inputs, never model-generated identity
or expected-answer text in the prompt. Approval results are non-durable required
markers; actual durable authorization is tested separately through HTTP/Postgres.

Compared with Day 8, the system now uses schema-constrained JSON, not just JSON
object mode. Groq GPT-OSS uses low reasoning effort and max_tokens=1200; Ollama
uses its JSON schema format, think=false, num_predict=600, context 4096 and
keep_alive=0. Limits remain six graph nodes/six reads/120s active run budget,
with at most 60s per model call. Local qwen3 was unloaded after evaluation.

Both Day 10 runs use dataset hash
6c4aa8840f41faeb9ceed6db194fe2065d9391cc21c87b4836f40f8b98d2dc03
and order fixture hash
edde792c6e67bcb3b1e81d780154cb3795b52cc1e5f3bdfd14bc2b579ddc7aee.
The original Day 7/8 dataset is preserved as scenarios-day07.jsonl. One expectation
was corrected before these runs: s023 may terminate at a tenant-bound foreign-order
404, instead of requiring a foreign order to reach downstream policy checks.
Its pure policy mismatch tests remain intact. No infrastructure error can score
as a successful refusal.

These are measured application configurations, not evidence that qwen3 is generally
better than GPT-OSS or that LangGraph alone improved reasoning. Original source/
order field checks do not establish semantic completeness. Schema enforcement
prevented malformed structures but did not prevent unnecessary escalation or
invented evidence ids; the code rejected those outputs.

## Security and runtime evidence

- [Eight injection checks](day-10-injections.json) pass for ticket instructions,
  poisoned articles/order notes/tool output, amount/tenant manipulation, fake
  approval and forged resume. The model is deliberately simulated as hostile;
  this tests authorization under adverse outputs, not live-model prompt immunity.
- [Postgres restart](day-10-postgres-restart.json): separate start/resume processes,
  no model replay after approval, unapproved execution blocked, one receipt after
  repeated resume. Synthetic operator and tenant, removed after testing.
- [Local container HTTP smoke](day-10-local-container-smoke.json): health/readiness,
  missing auth, durable pause, tenant/scope/forged-resume rejection, distinct operator
  decision, actual internal HTTP execution and exactly one receipt. Synthetic
  fixture removed; no seeded demo request approved or altered by this test.
- **308 tests passed in 31.47s**, including local Postgres integration and both
  checkpoint restart modes. Lint/format clean. Both new non-root Docker images
  build; image inspection confirmed no .env or Git history. Local memory snapshot:
  agent 97.98MiB/384MiB, backend 61.93MiB/256MiB. Not a peak or EC2 load test.

Service code and CI/deployment files await the user's commit/push. EC2 remains on
the earlier Knowledge API release; no Day 10 cloud schema or deployment change
has been made yet. G2 deployment/remote CI checks remain open. Learning checks
remain deferred. See [G2 checklist](../../docs/gates/G2-verification.md).

Provider references checked against current official docs:
[Groq structured outputs](https://console.groq.com/docs/structured-outputs) and
[reasoning effort](https://console.groq.com/docs/reasoning).
