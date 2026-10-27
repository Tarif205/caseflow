# CaseFlow portfolio and interview preparation

## Project description

CaseFlow is an AI-assisted, two-tenant support platform. A cited Knowledge API and
read-only MCP tools supply policy and order evidence to a LangGraph agent. A
separate operator must approve eligible mock refunds before an internal backend
rechecks policy/authority and records an idempotent receipt. Python services run
in Docker on AWS EC2 with Neon Postgres/pgvector and GitHub Actions CI.

Repository: https://github.com/Tarif205/caseflow. Architecture, evaluations and
public verification are linked from the root README. A recording is not yet made.

## Draft CV bullets backed by evidence

Adapt these after studying the implementation. Describe this accurately as an
AI-assisted project; these bullets are project outcomes, not an assessment of
independent coding ability. Do not claim production traffic or real payments.

- Developed an AI-assisted support platform with 3 core Python services and an
  internal mock backend; deployed Docker services on AWS EC2 with Neon Postgres,
  scoped bearer authentication and tenant-filtered reads.
- Evaluated 384-dimensional pgvector retrieval over 18 articles/36 chunks, reaching
  Recall@5 of 1.000 on 40 synthetic development questions; documented in-sample
  tuning and answer-quality limitations.
- Integrated LangGraph with read-only MCP tools; a hosted evaluation passed 22/25
  support scenarios (88%), with failures and provider rate-limit retries retained.
- Verified 370 automated tests including Postgres integration, plus 16/16 deterministic
  injection enforcement checks across 8 surfaces and 2 tool adapters.
- Implemented durable operator approval and transactional mock-refund idempotency;
  public HTTP smoke verified pause/resume and exactly 1 receipt after retry.
- Built CI checks for lint, formatting, tests, 4 Docker images and deployment
  configuration/rollback; documented recovery from a cloud-readiness timeout.

Evidence and qualifications for every number: [results](RESULTS.md).
Do not describe the historical 84% direct versus 88% MCP results as a causal quality
improvement. The 25/25 paired replay used the same model decisions.

## Ten-minute walkthrough script

| Time | What to explain/show | Code or evidence |
|---|---|---|
| 0: 00-1: 00 | Fictional support problem; user vs operator permissions; what the model may propose | Root README architecture |
| 1: 00-2: 30 | Article ingestion: character chunking, title-prefixed CPU embeddings, tenant-filtered vector search | src/caseflow/chunking.py, ingestion.py, database.py |
| 2: 30-3: 30 | Validated quotes/citations; why a related policy is not proof of a customer's order status | answering.py and decision 002 |
| 3: 30-5: 00 | LangGraph state/nodes, budgets, read tools; fixed MCP registry and bound credentials | agent_graph.py, mcp_client.py |
| 5: 00-6: 30 | Pause, stored proposal, separate approval, resume, current facts, one receipt | durable_agent.py, approvals.py; public smoke |
| 6: 30-7: 30 | Tools vs resource vs prompt; stdio vs stateless HTTP; tenant context | mcp_server.py, mcp_http.py |
| 7: 30-8: 30 | Local Docker vs EC2; Caddy TLS; Neon; SSM and instance IAM role; CI vs manual deployment | deploy-mcp.md, workflow YAML |
| 8: 30-9: 30 | Quality numbers, scope limits, rate failures and cloud recovery incident | RESULTS.md, decision 008 |
| 9: 30-10: 00 | What was AI-assisted; what you can reproduce; next learning priorities | Your study notes |

Use this while practicing. The gate requires a later attempt **without notes**;
reading this script does not pass it.

## Interview questions to practice

1. Trace one request from Caddy through an authenticated tenant query to its response.
2. Why do embeddings have384 dimensions, and what does cosine distance measure?
3. Why do SQL filters and foreign keys still matter after authenticating a token?
4. What is the difference between retrieval recall and generated-answer correctness?
5. What does an LLM tool call request, and where is authority actually enforced?
6. What does LangGraph persist during an interrupt? Why can't resume JSON approve?
7. What prevents two simultaneous resumes from issuing two mock refunds?
8. Why is the operator token excluded from the model and MCP read tools?
9. How do MCP tools, resources and prompts differ? What does stateless HTTP imply?
10. What does a green CI run establish? Why is deployment a separate action here?
11. Why did the first cloud readiness probe fail although CI passed?
12. Why restore the old Compose topology as well as old images during rollback?
13. How would you add reviewed held-out scenarios, load tests and production auth?
14. Which parts did AI help implement, and which can you now explain/rebuild alone?

Record unanswered questions below after each rehearsal. No rehearsal is claimed yet.

| Date | Question you could not answer | File/topic to study | Re-test outcome |
|---|---|---|---|
| Pending | First no-notes rehearsal not performed | Learning roadmap | Unassessed |

For a starting order, use [the learning roadmap](LEARNING_ROADMAP.md): Python/HTTP,
SQL and testing, FastAPI, Docker/Git/CI, embeddings/RAG, tool calling/LangGraph, MCP,
then AWS/IAM/operations. Rebuild one small flow at a time after finishing the demo.
