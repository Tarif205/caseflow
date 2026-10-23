# Day 3 technical record

Date: 22 October 2026. Assistant implementation under the user's override.
Learning and explain-back checks remain deferred.

## Implemented

- Expanded the synthetic development dataset to 40 answerable and 10 unanswerable
  questions, with validation for fields, ids, labels and duplicate entries.
- Metrics for Recall@5, MRR@5, top-1 article accuracy and context cutoff k.
- Five controlled experiments: baseline 800/120/k5, smaller chunks 400/120/k5,
  larger chunks 1200/120/k5, zero overlap 800/0/k5 and context 800/120/k3.
- An explicit in-sample score threshold sweep measuring answerable acceptance,
  unanswerable rejection and balanced accuracy, separately from retrieval ranks.
- Temporary evaluation tenant copies with forced transaction rollback; public
  corpus data is not replaced and reserved-name collisions fail safely.

## Measurements

All five runs achieved Recall@5 of 1.000 on the 40 answerable questions. Baseline
MRR@5 was 0.950 with 90% top-1 accuracy. Larger chunks reached MRR@5 1.000 and 100%
top-1 accuracy, using one chunk per article in this small corpus.

Larger chunks had a worse threshold tradeoff than the zero-overlap configuration:
at their in-sample selected threshold around 0.69435, 9/10 unanswerable questions
were rejected, but 5/40 answerable questions were also rejected. The refund-date
question q047 still passed because related refund policy text scored highly.
The zero-overlap setting retained 95% of answerable questions at the same 90%
unanswerable rejection, with MRR@5 0.9875.

These are synthetic development results. The single expected-article label may
penalize another article that repeats the same fact. No independent label review,
held-out performance, generated-answer quality or production threshold is claimed.

## Verification

- 91 tests passed, including metric edge cases, malformed datasets and real Postgres
  experiment rollback/preservation tests. Lint and formatting checks passed.
- All five configurations repeated identical rankings and rounded scores, both
  within the runner and on an independent full rerun. Input hashes also matched.
- Original corpus remained 30 Northwind chunks and 6 Contoso chunks. No temporary
  evaluation tenants remained after the run.
- Full evidence: `evals/results/day-03-retrieval.json` and its Markdown summary.

## Next step

Day 4 Knowledge API with authentication, scopes, citations, refusal behavior,
tests, Dockerfile and CI. The importer still uses 800/120 until the API's
answer/refusal tests justify an operating choice. No commit, push, CI run, hosted
model call, or public deployment was performed in this stage.
