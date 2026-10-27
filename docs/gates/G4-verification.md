# Gate G4: portfolio verification

Date: 28 October 2026. **Open: recording and learner rehearsal are pending.**
Implementation-first authorization remains in effect. Documentation or an automated
check must never be treated as proof of independent understanding.

| Requirement | Current evidence | State |
|---|---|---|
| Four service READMEs, architecture and decisions | Root README links four services; architecture diagram and eight decision records | Prepared |
| Results backed by saved evaluations | [Results](../RESULTS.md), all metric rows link original reports and limitations | Prepared |
| CV bullets with at least four measured numbers | [Portfolio](../PORTFOLIO.md): 370 tests, 22/25 scenarios, 384 dimensions, 18 articles/36 chunks, 16 enforcement checks | Prepared; personal mastery unassessed |
| Fresh checkout follows README in under 20 minutes | [Isolated clean-clone report](../../evals/results/day-14-clean-clone.json); see scope below | Automated service check passed; manual README-only acceptance pending |
| Secret scan of repository and history | [Targeted scan](../../evals/results/day-14-secret-scan.json): 482 reachable blobs, configured private values and common credential patterns, Office XML included; zero matches | Passed within stated scan coverage |
| Three-minute screen recording | [Storyboard and commands](../DEMO.md) | User recording/review/link pending |
| Ten-minute walkthrough without notes and unanswered questions | [Script and study-log table](../PORTFOLIO.md) | Deferred/unassessed; never passed |
| AWS cleanup and current free-plan review | Existing deployment preserved; last user screen reported 14 April 2027; no current balance/unused-resource audit claimed | User console review pending |

The automated check passed. Active build/check attempts totaled 346.28s including
harness retries; the final corrected run took 56.44s. These timings exclude tool
installation and editing gaps. Initial ad hoc SDK keyword errors are retained in
the report; no application code change was needed. The temporary stack/volumes and
image tags were removed; all five original local services remained healthy.

## Scope of the fresh-checkout check

Committed source is cloned locally with git clone --no-local. No private .env or
installed virtualenv is copied. New Compose project/database/model-cache volumes,
loopback 18011/18012/18013 and no DB host publishing avoid the existing development
stack. All four service images are built from that checkout. Tool installation
and a previously populated host Docker build cache are excluded from elapsed time.
The isolated stack is removed afterward; original services/volumes are preserved.

Startup initializes Postgres checkpoints/mock fixtures and imports both corpora.
The check covers health/readiness, missing MCP bearer rejection, and real SDK tool,
resource and prompt calls for both tenants. The model key is blank; no fresh hosted
inference, refund or recording is claimed. The existing Day 13 public workflow proof
is separate. New README commands are a reviewed draft; the automated harness uses
an explicit port/project override and in-container CLI instead of a new host uv
installation. A person's timed README-only run is still required for that gate item.

## Next user actions

1. Record and review the three-minute demo using ../DEMO.md; add its actual URL.
2. Run the ten-minute walkthrough without notes; record unknowns for later study.
3. Complete a timed README-only run and current AWS billing/resource review.
4. Commit/push the portfolio and evidence; keep manual/deferred items honest.

No cloud deployment is required for these documentation changes. Do not remove
EC2 data, certificates or active resources as speculative cleanup.
