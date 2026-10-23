# Initial chunking baseline

Date: 22 October 2026

## Context

Day 2 requires a simple, deterministic chunker before retrieval quality is measured.
The corpus consists of 15 fictional Northwind articles and 3 Contoso isolation
fixtures. The embedding model is BAAI/bge-small-en-v1.5 with 384 dimensions.

## Options

1. Fixed character windows with explicit overlap and offsets.
2. Heading-aware splits that preserve sections but need a separate oversized-section rule.
3. Token-aware splits aligned to the embedding model's tokenizer.

## Decision

Start with 800-character windows and 120-character overlap. Preserve the exact source
substring and its start/end offsets in the chunker output. Omit whitespace-only
windows and number retained chunks consecutively. Prefix the article title only
when embedding each chunk, so later windows retain article context.

This baseline is small and easy to reproduce for the upcoming experiments. It is
not claimed to be the best retrieval configuration. It may split words and does
not enforce the embedding model's token limit on arbitrary text. The character
offsets are currently in chunker output, not stored in the SQL schema; database
citations can use stable chunk ids, article ids and positions.

## Consequences

- The default settings yield 30 Northwind chunks and 6 Contoso chunks.
- Long lines are bounded and overlapping windows preserve their non-whitespace text.
- IDs are stable for the same tenant, document and chunk position. Changing chunk
  boundaries can change the content associated with a position; citations are not
  immutable versioned records across re-ingestion.
- Re-imports replace supplied documents atomically. Files absent from the batch
  remain in the database, avoiding implicit deletion of unrelated documents.

## Verification and next decision

Tests cover exact overlap, empty input, long lines, Unicode offsets, invalid settings,
batch rollback, stale-chunk replacement and tenant separation. Two real imports
produced identical stored text, ids and counts. Day 3 will compare configurations
using retrieval metrics; no accuracy claim is made from the chunk counts alone.
