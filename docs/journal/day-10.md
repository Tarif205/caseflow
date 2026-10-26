# Day 10: evaluation, injection checks and release preparation

Date: 26 October 2026. User authorized implementation first; learning checks deferred.

Added strict schema-based graph outputs and safe provider diagnostics (HTTP status,
known error code, timeout/token limit; no error bodies). GPT-OSS uses low reasoning
and 1200 output tokens. A single bounded Retry-After retry handles confirmed 429s.
Preserved the initial hosted run and then measured a slower paced run.

Full 25-case results: hosted initial 14/25 with eight HTTP 429 failures; hosted
paced **21/25 (84%)**; local qwen3 **22/25 (88%)**. Failures remain in each artifact.
Immutable orders and explicit trusted fixture context avoid the completed Day 9
demo changing test inputs. One foreign-order expectation was fixed before runs;
the original Day 7/8 dataset is preserved. These are synthetic development results,
not a held-out or intrinsic model ranking. qwen3 unloaded after evaluation.

Added eight hostile-output/data injection enforcement cases; all passed without
unauthorized action. Added Postgres checkpointer and separate-process restart
verification; simulated approved run resumed without a model replay and left one
receipt. Added tenant/scope-bound HTTP agent routes, strict operator decisions and
opt-in internal mock refund route reusing the authoritative ledger. Incoming worker
credentials are forwarded to the same-tenant read services; no model chooses them.

**308 tests passed in 31.47s** with Postgres and both checkpoint modes. New service
Dockerfiles build non-root images with no .env or Git history. CI now builds all
three images. Local containers passed real hosted HTTP workflow smoke through
agent API, Postgres and internal backend: pause, blocked unapproved execution,
simulated operator approval, resume and exactly one receipt after retry. Temporary
fixture removed. Idle snapshot: agent 97.98MiB, backend 61.93MiB; not a load test.

Prepared local/AWS Compose files, explicit cloud hash/schema provisioning helper,
reviewed-commit EC2 deploy helper and rollback notes. Read-only SSH confirms current
remote code 531d7c4. No Day 10 cloud schema, role or service deployment changes yet.
The user's commit/push and fresh CI are the next release step, followed by EC2
deployment and public authenticated smoke. G2 remains open until those are verified.
No assistant commit/push, new paid resource or plan upgrade.

## Release deployed after user push

The user pushed 47906e1; Actions run 40340314622 passed. Neon additive schema,
checkpoints, fixtures and role-token hashes provisioned without exposing secrets.
An automatic-review usage failure initially prevented deployment; after the user
said carry on, the same command passed review and deployed the exact commit.

EC2 now runs agent/backend images tagged 47906e1b13ea, with agent loopback 8002
and no backend public port. Caddy persistently serves /agent while preserving
Knowledge API 531d7c4. Old proxy retained stopped for rollback; cert volumes reused.
Public synthetic HTTP smoke passed pause/auth/approval/resume/idempotency and
removed its own Neon rows/checkpoints. The original Knowledge API full smoke
also passed, including actual cited model output. No real/demo approval performed.

Saved release CI, EC2 metadata, public agent and preserved-Knowledge smoke JSONs.
EC2 snapshot MiB: Knowledge 236.9, agent 91.89, backend 59.64, proxy 10.42.
G2 technical release checks verified; manual trace screenshot/explain-back deferred.
Cloud tracing remains off; do not infer it from local Langfuse proof. Next technical
work: Day 11 MCP. User saves evidence/docs with their normal commit/push.
