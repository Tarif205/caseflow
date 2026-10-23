# Day 1 technical record

Date: 22 October 2026. Implementation by the assistant under the user's workflow override.
Learning checks remain deferred.

## Implemented

- Root Python package and locked dependencies, a Docker Compose local Postgres 16
  database with pgvector, health check, persistent volume and loopback-only port.
- Idempotent schema for tenants, hashed API token records, documents and 384-dimensional
  chunk embeddings. Composite keys prevent cross-tenant document references.
- Lazy FastEmbed CPU adapter using the existing G: model cache and query-specific
  encoding. Invalid, non-finite and zero-norm embeddings are rejected.
- Parameterized cosine-distance SQL with mandatory tenant and model filtering.
  Repeat document ingestion replaces chunks atomically without affecting other tenants.
- CLI database initialization and five-question search check using three fictional
  policy articles. No model chat calls or cloud database mutations were required.

## Verification

- 26 automated tests passed, including a separate local `copilot_test` database.
- Real embeddings ranked the expected article first for 5/5 questions. Saved output:
  `evals/results/day-01-search.json`.
- This small result is a sanity check, not the Day 3 retrieval evaluation.
- Local extension version: 0.8.7. The earlier Neon result was 0.8.6; they are separate
  databases. Both use 384-dimensional vectors in this project.

## Limits and next step

The full Knowledge API, token validation, content ingestion pipeline, support agent,
MCP server, full evals and public deployment remain pending. Day 2 adds the fictional
article corpus, chunker and ingestion pipeline. No independent learning, CI run,
deployment, commit or push is claimed.
