# Gate G1 technical verification

Date: 26 October 2026 (Asia/Dhaka).

**Technical requirements verified; original learning explain-back deferred.**
The user authorized implementation first and study afterward. Do not interpret
this record as passing that learning check or independently mastering the work.
Latest clean-checkout evidence/report await the user's normal commit/push.

## Evidence

| Requirement | Result | Evidence and limit |
|---|---|---|
| Recall@5 >= 0.70 on 40 questions | 1.000 | [Day 3 development evaluation](../../evals/results/day-03-retrieval.md); synthetic in-sample questions, not held-out |
| API refuses >= 70% of 10 negatives | 10/10, zero HTTP errors | [Actual public API run](../../evals/results/day-05-public-refusals.json); eight no_evidence and two record_lookup_required before generation |
| Tests locally and in CI, tenant tests included | 153 local tests passed in 8.46s; user reports green CI for 7c2f4fe | Full local run includes integration tests against separate copilot_test; cloud serving image is 531d7c4, later changes are operator tooling/docs |
| Compose works from a clean checkout | Passed | [Fresh-clone artifact](../../evals/results/day-05-clean-clone.json); isolated host ports, DB/cache volumes and temporary generated test tokens |
| Public answer with citations | Passed | [Public HTTPS smoke](../../evals/results/day-05-public-https-smoke.json); actual Groq generation, source quotation verified |
| Recovery after restart | Passed manual container restart and public smoke | [Post-restart result](../../evals/results/day-05-public-after-restart.json); no automatic crash/reboot recovery claim |
| Stack without guest swapping | Guest has zero swap configured | User memory output: API 348.9 MiB, proxy 11.14 MiB; 1.1 GiB host RAM available; snapshot, not peak/concurrency testing |
| Draw/explain pipeline without notes | Deferred | Explicit user workflow override; never marked passed |

The data/metrics preceding the fresh-clone report were committed in 7c2f4fe.
No full 40-question generated-answer/semantic-faithfulness benchmark is claimed.
The positive smoke is one real warranty question. There is no production
hardening, rate-limiting or availability guarantee implied by this gate review.

## Fresh-checkout procedure and boundaries

Cloned committed main from the local Git repository with `git clone --no-local`,
yielding exactly 7c2f4fe349eb0c1ee82e77e5f644e74c29da6c19. No .env, installed
virtual environment, working-tree edits or cloud credentials were copied.

Used separate project `copilot-verify-7c2f4fe` and `--env-file .env.example`.
The development stack already occupied ports 8001/5432, so this untracked
verification override changed only image naming/host port publishing and forced
an empty model key. It did not change ingestion, schema, API or retrieval code:

```yaml
services:
  db:
    ports: !reset []
  knowledge-api:
    image: support-copilot-clean-7c2f4fe:verify
    ports: !override
      - "127.0.0.1:18011:8000"
    environment:
      LLM_PROVIDER: ollama
      LLM_MODEL: qwen3:4b
      LLM_API_KEY: ""
```

Local Compose version: 5.6.0, which supports these override tags. In that clean
checkout, the startup command was:

```text
docker compose -p copilot-verify-7c2f4fe --env-file .env.example -f compose.yaml -f compose.verify.yaml up -d --build --wait --wait-timeout 300
```

Fresh model and database volumes were created. Startup built the runtime image,
initialized the schema and ingested 15 Northwind articles/30 chunks and 3 Contoso
articles/6 chunks. Health/readiness succeeded both inside the container and via
the host's published port. Missing-token search returned 401. Temporary generated
read tokens authenticated real searches, whose returned text matched only their
respective tenant's original source files. Tokens were not printed or persisted
to source/config files; only hashes entered the disposable test DB.

A separate in-process TestClient application inside the same runtime image used
deliberately incorrect demo DB credentials. Health still returned 200; readiness
returned 503 without the password in its body. Request logs showed the failing
route/status without revealing credentials. This did not change the running
service's environment or a real password.

No chat-model call was made in the fresh local stack; actual chat generation is
verified separately by the deployed public smoke. This clean checkout checks
bootstrapping and API/retrieval operation, not an unconfigured Ollama server.

After saving the evidence, `down --volumes` removed only this uniquely named
test project's containers, network and volumes. The original development stack,
Neon data, EC2 containers and user's .env were left unchanged. The ignored clone
and build cache can remain as verification artifacts; no real data was deleted.

## Next step

Proceed to PRD Day 6: synthetic orders/tickets backend, first scenarios and a
bounded tool loop. Keep every refund behind the code-enforced approval path.
Preserve tenant isolation and free-tool constraints. User commits/pushes the
latest evidence in their normal workflow; assistant made no commit/push.
