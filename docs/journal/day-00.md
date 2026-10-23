Date / Day number: Setup completed across sessions through 22 October 2026 / Day 0

## Technical record

This record was maintained by the assistant from verified checks and the user's
reports. It does not represent an independent learning assessment.

- Docker: `health-app` was built and run; the assistant verified its published port
  and `/health` returned `{"status":"ok"}`. The user then stopped the container.
- Embeddings: the earlier three-sentence experiment produced 384-dimensional
  vectors. Recorded related-pair similarity was 0.740, with unrelated pairs
  scoring 0.457 and 0.418.
- Tool calling: the model requested an order lookup for order 1042 and avoided
  requesting one for a geography question. Reasoning leaked into output despite
  `think=false`. No real lookup or complete agent loop was implemented in this check.
- Langfuse: `hello/langfuse_check.py` was saved and syntax-checked. The user
  confirmed `day-0-check` appeared with the expected input and output in Langfuse.
  Installed versions: langfuse 5.0.4 and python-dotenv 1.2.4.
- Neon: the user ran the extension query and reported vector version 0.8.6.
- Model memory measurement from the setup sessions: approximately 0.6 GB free RAM
  while qwen3:4b was loaded. Run one heavy component at a time.

## Understanding and workflow

The user said the setup felt like following instructions without understanding.
Independent understanding, explain-backs and skill ratings remain unverified.
On 22 October the user explicitly chose to finish the working project first,
study it afterward, and let the assistant implement the core code and tests.
Learning checks are deferred, not marked passed. AWS remains deferred to deployment.

## Debugging evidence

The Docker build initially ran from the repository root. The Dockerfile was in
`hello/health_app`, so Docker could not find it in the selected build context.
Changing to that folder allowed the build to complete.

## Next work

Implement and verify the Day 1 local Postgres/pgvector foundation, then continue
through the PRD dependency order. Commits and pushes will be done by the user.
Hours: not recorded. No commit is claimed for this entry.
