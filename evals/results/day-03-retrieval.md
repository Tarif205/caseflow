# Retrieval development results

Measured at: 2026-10-22T14:54:40.529719+00:00

Synthetic assistant-authored development set: 40 answerable and 10 unanswerable questions.
Labels are not independently reviewed. These are in-sample results, not a held-out benchmark.

| Experiment | Chars | Overlap | Context k | Northwind chunks | Recall@5 | MRR@5 | Top 1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 800 | 120 | 5 | 30 | 1.000 | 0.950 | 0.900 |
| smaller-chunks | 400 | 120 | 5 | 51 | 1.000 | 0.950 | 0.900 |
| larger-chunks | 1200 | 120 | 5 | 15 | 1.000 | 1.000 | 1.000 |
| no-overlap | 800 | 0 | 5 | 30 | 1.000 | 0.988 | 0.975 |
| top-three | 800 | 120 | 3 | 30 | 1.000 | 0.950 | 0.900 |

## Score gate calibration

The threshold is selected in-sample for maximum balanced accuracy. It does not measure LLM answers.

| Experiment | Threshold | Answerable accepted | Unanswerable rejected | Balanced accuracy |
|---|---:|---:|---:|---:|
| baseline | 0.691243 | 0.925 | 0.900 | 0.913 |
| smaller-chunks | 0.698769 | 0.925 | 0.900 | 0.913 |
| larger-chunks | 0.694348 | 0.875 | 0.900 | 0.887 |
| no-overlap | 0.691243 | 0.950 | 0.900 | 0.925 |
| top-three | 0.691243 | 0.925 | 0.900 | 0.913 |

Recommended configuration: {"chunk_size": 1200, "name": "larger-chunks", "overlap": 120, "top_k": 5}.
This recommendation optimizes retrieval ranks only. Its score gate can reject more answerable questions than another setting.
The imported corpus and default importer settings remain at the Day 2 baseline pending API-level evaluation.

All experiments reproduced identical rankings and rounded scores on a second query pass.
Temporary evaluation tenants were rolled back; the imported corpus was not replaced.

Recall@5 and MRR@5 use chunk positions, including repeated chunks from one article.
The top-three experiment still fetches five hits for comparable @5 measurements; context uses three.
The full per-question rankings, threshold sweep, package versions and input SHA256 are in day-03-retrieval.json.
