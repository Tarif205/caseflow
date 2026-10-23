# Day 2 technical record

Date: 22 October 2026. Assistant implementation under the user's override.
Independent learning checks and explain-backs remain deferred.

## Implemented

- 15 fictional Northwind help articles and 3 Contoso articles with deliberately
  different policies and overlapping document ids.
- Character-window chunker with configurable size and overlap, exact source offsets,
  preserved whitespace and support for long unbroken lines.
- Validated Markdown loader and trusted-admin ingestion CLI. Article titles provide
  embedding context; source text remains unchanged for citations.
- Batch-wide rollback and idempotent document replacement. Re-imports remove obsolete
  chunks for supplied documents while preserving other documents and tenants.
- 20 assistant-authored candidate retrieval questions with expected document ids.
  These need label review and are not a held-out human-authored benchmark.

## Verified

- 64 automated tests passed, including the real local Postgres integration suite.
- Real embedding imports yielded 15 documents / 30 chunks for Northwind and
  3 documents / 6 chunks for Contoso.
- Importing twice produced identical source-text hashes, stable chunk ids and counts.
- A query mentioning Contoso was searched under both tenants. Returned text was
  checked against the requested tenant's source files and remained isolated.
- The Day 1 demo was moved into its own tenant; a regression test proves it cannot
  overwrite the full Northwind return policy.
- Lint and formatting checks passed. No cloud calls, commits or pushes were made.

## Evidence and next step

Results: `evals/results/day-02-ingestion.json`.
Decision: `docs/decisions/001-chunking.md`.

Next is Day 3: complete the 40 answerable and 10 unanswerable question set, implement
the evaluation runner, record the baseline and compare retrieval configurations.
The public Knowledge API, agent, MCP, CI and deployment remain pending.
