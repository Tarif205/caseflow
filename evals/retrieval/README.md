# Retrieval development evaluation

Run from the repository root after starting and initializing the local database:

```powershell
uv run --frozen python evals/retrieval/run.py
```

Outputs are `evals/results/day-03-retrieval.json` and the readable Markdown summary
beside it. No chat model or hosted inference is used. A remote database URL is
rejected. The runner uses the installed FastEmbed model and local Postgres.

## Data and labels

The JSONL set contains 40 answerable and 10 unanswerable Northwind questions.
These questions and articles were authored by the assistant for this project.
Expected article labels have not had independent human review. All configurations
and score thresholds are compared on this same synthetic development set; the
results are not held-out estimates of performance on real customer tickets.

An answerable example names one expected article. Some other articles repeat parts
of the same policy, so an unexpected top article is not necessarily a false factual
answer. This evaluation measures the labeled article's retrieval rank, not answer
correctness or faithfulness. Unanswerable examples include both out-of-domain topics
and requests for unavailable order-specific data.

## Metrics

- Recall@5: fraction of the 40 answerable questions whose expected article appears
  among the five highest-ranked chunks.
- MRR@5: average reciprocal rank of the first chunk from the expected article,
  assigning zero when no such chunk occurs in the top five.
- Top 1: fraction whose first chunk comes from the expected article.
- Recall@k and MRR@k: the same calculations at the chosen context size.
- Score-gate acceptance/rejection: whether the highest chunk score is at least the
  threshold. A rejected question is not passed on to answer generation. These are
  not generated refusal or faithfulness measurements.

Duplicate chunks from an article occupy separate ranks. The top-three experiment
still fetches five hits to make @5 metrics comparable, then measures context @3
separately. The recommended retrieval configuration maximizes Recall@5, then MRR@5,
then top-1 accuracy, with fewer chunks breaking ties.

## Experiments and reproducibility

Baseline: 800 characters, 120 overlap, context k=5. Separate experiments change
only chunk size to 400 or 1200, overlap to zero, or context k to three. Article-title
prefixing, corpus, model and query encoding stay fixed.

Each configuration imports isolated temporary copies inside a transaction that
always rolls back. Existing reserved evaluation tenants cause a safe failure.
The real Northwind and Contoso rows remain unchanged. Rankings and scores rounded
to eight decimal places are checked on a second SQL query pass. An additional full
rerun was checked for matching rankings, rounded scores, metrics and input hash.
Package versions and the input SHA256 are saved in the JSON result. Reproducibility
was verified on this machine and model cache, not promised across hardware or model
weight revisions.

## Calibrating not found

Candidate thresholds lie midway between observed top scores, plus extremes that
accept everything or reject everything. Selection maximizes balanced accuracy:
the average of answerable acceptance and unanswerable rejection. Ties prefer
answerable acceptance, then the lower threshold. Calibration is in-sample.

Larger chunks ranked the expected article first for all 40 answerable examples,
but their selected gate rejected 5 answerable examples and accepted one
unanswerable request for an exact refund date. A related article cannot supply an
order-specific fact it does not contain. The upcoming answer endpoint needs
grounded generation and separate answer/refusal evaluation. No production score
threshold is claimed here, and importer defaults are intentionally unchanged.
