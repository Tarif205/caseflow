# Support Copilot learning roadmap

Updated: **23 October 2026**. Companion: [project walkthrough](PROJECT_EXPLAINED.md).

This roadmap covers the full intended project, including unfinished features.
It is a study sequence, not a claim that you already know these subjects. It does
not replace the PRD's implementation gates or require quizzes before continuing
authorized work. Learning checks are **deferred**, not passed.

## 1. The short answer about CI/CD

The official name for the GitHub check we used is **continuous integration (CI)**.
The automation tool is **GitHub Actions**. Its YAML file defines a **workflow**;
each execution is a **workflow run** containing a **job** that runs **steps** on a
**runner**. Our job installs dependencies, checks code, runs tests and builds an
image. It uses a **service container** for the test database.

We currently deploy manually. **Continuous delivery** adds a repeatable path for
releasing validated software, potentially with a human release decision.
**Continuous deployment** automatically deploys passing changes. GitHub Actions
can support both, but our current green check does not deploy to AWS.

Official reference: [Understanding GitHub Actions](https://docs.github.com/en/actions/get-started/understand-github-actions).
Read the actual [workflow](../.github/workflows/ci.yml) beside the explanation in
[walkthrough section 10](PROJECT_EXPLAINED.md#10-git-github-and-the-green-check).

## 2. How to use this roadmap without studying everything at once

Use a separate local learning folder/repository, such as `G:\support-copilot-labs`.
Exercises that deliberately break things belong there, not in the deployed service
or hosted database. Cloud exercises are optional until prerequisites are comfortable;
local practice is enough for most phases.

For a study session, aim for a manageable block such as:

1. 15–25 minutes of one focused lesson or documentation section.
2. 25–45 minutes building a small variation yourself.
3. 10 minutes inspecting an error and recording what caused it.
4. A short note linking the concept to one file in Support Copilot.

These times are suggestions, not deadlines. Repeat a phase or spread it over more
sessions. You do not need to finish a 19-hour course before writing a health route.

For each exercise, try: follow an example once, close it, rebuild a small version,
change one requirement, then deliberately break and repair it. Use references
when stuck. Progress means being able to make and diagnose changes, not memorizing
every command or avoiding documentation.

No one course covers this entire project. CS50P develops Python foundations;
FastAPI, Docker, GitHub Actions, cloud deployment and agent frameworks require
their own material. Flask lessons teach transferable HTTP ideas but do not teach
FastAPI's exact routing/dependency/Pydantic APIs.

## 3. Overview and prerequisites

| Phase | Official topic | Prerequisites | Connects to |
|---|---|---|---|
| 0 | System architecture and execution environments | None | Knowing which machine runs a command |
| 1 | Python programming and dependency management | Basic variables/loops helpful | All service code |
| 2 | Linux, shells and filesystem permissions | Phase 0 | Ubuntu, SSH and local terminals |
| 3 | Git and version control | Files and terminal basics | Commit/push/clone and collaboration |
| 4 | Networking, HTTP and REST-style APIs | Phases 0–2 | FastAPI, ports, clients and servers |
| 5 | Backend development with FastAPI and Pydantic | Python + HTTP | Routes, validation and dependencies |
| 6 | Relational databases and PostgreSQL | Python + basic backend concepts | Storage, transactions and tenant filters |
| 7 | Automated testing and code quality | Python + the component being tested | pytest, Ruff and reliable changes |
| 8 | Containerization with Docker and Compose | Shells + HTTP + application basics | Images, containers and local services |
| 9 | CI/CD and GitHub Actions | Git + tests + basic Docker | The green check and future releases |
| 10 | Cloud deployment and application operations | Phases 2–9 | EC2, SSH, secrets, HTTPS and recovery |
| 11 | Embeddings, semantic search and RAG | Python + SQL + API basics | Knowledge API internals |
| 12 | Evaluation and observability for AI applications | RAG + testing | Quality evidence, logging and traces |
| 13 | Tool calling and agent loops | Python + APIs + RAG | Planned support agent |
| 14 | LangGraph, persistence and human approval | Tool loops + testing + DBs | Planned durable approval workflow |
| 15 | MCP and multi-tenant tool security | APIs + authorization + tool calling | Planned read-only MCP server |
| 16 | Integration, release verification and portfolio evidence | Relevant earlier phases | Finishing and explaining the system |

Some phases can overlap. In particular, learn testing while learning Python/API/SQL,
and learn basic security while implementing each boundary. Phases 0–10 explain
the deployment steps we have just performed; phases 11–16 cover the AI application
and remaining project. You may study phase 11 before cloud deployment once SQL
and Python are comfortable. This learning order does not authorize skipping PRD gates.

## 4. The first three study sessions

This is the small entry path. The rest of the roadmap is reference material.

| Session | Read/watch | Do | Expected result |
|---|---|---|---|
| 1: Where code runs | Walkthrough sections 1–4 | Draw laptop, GitHub repository, CI runner and EC2 as four separate boxes | You can place `git push`, tests, SSH and the Docker build on the correct machine |
| 2: Source history | Git beginner resource below | In a practice repository, edit a text file, stage, commit and inspect `git log`/`git show` | You can distinguish an uncommitted change from a saved commit |
| 3: The green check | Walkthrough section 10 and GitHub Actions concepts | In a public disposable lab repo, run one tiny Python test from a workflow, then intentionally fail the assertion | You can identify the event, job, step, runner and failure log |

That first workflow can use GitHub's current Python workflow example. It does not
need Docker, AWS secrets or this project's database. Once the small version makes
sense, compare it with our real workflow.

## 5. Phase 0 — Architecture and execution environments

**Purpose:** stop treating a command as an unexplained action. Identify its input,
its machine, what it changes and what output would establish success.

**Subtopics:** operating system, terminal versus shell, local versus remote,
process versus file, client/server, development/test/deployment environments,
source code versus package versus running service, data flow versus deployment flow.

**Prerequisites:** none.

**Exercise:** draw two diagrams. First: developer edits -> GitHub -> CI -> EC2
checkout/image. Second: API request -> authentication -> retrieval -> model ->
citations. Mark which arrows already work and which are planned.

**Ready to advance when:** you can explain why a successful CI build does not
mean the public API has started, and why a second terminal can be on another machine.

**Resource:** the companion walkthrough and your real console/terminal history.
**YouTube search terms:** `client server architecture beginners`, `development testing production environments explained`.
These search terms are discovery prompts, not claims that a specific video was vetted.

## 6. Phase 1 — Python and dependency management

**Purpose:** understand the code inside the tools rather than only how to start it.

**Subtopics:** functions, loops, dictionaries/lists, comprehensions, exceptions,
modules/imports, file I/O, `pathlib`, type hints, dataclasses, interfaces/protocols,
context managers, JSON serialization, package installation, virtual environments,
`pyproject.toml`, `uv.lock`, environment variables. Learn basic async/concurrency
after synchronous code is comfortable; not every route needs `async def`.

**Prerequisites:** basic programming logic. Review only the gaps if CS fundamentals
are already familiar.

**Exercises:**

1. Read three Markdown files and return a list of dictionaries containing filename,
   title and text; give a useful error for a missing directory.
2. Write a small function that validates a list's length and rejects invalid items.
3. In the lab project, add a package, inspect the lock file and reproduce the environment.
4. Read a non-secret setting from the environment and demonstrate that a running
   process does not automatically reread an edited file.

**Project files:** `config.py`, `chunking.py`, `ingestion.py`, `pyproject.toml`.
**Ready to advance when:** you can write and test a small module, read a traceback,
and explain the difference between a dependency declaration and an installed package.

**Primary resources:** [CS50P](https://cs50.harvard.edu/python/) for Python fundamentals,
[uv project guide](https://docs.astral.sh/uv/guides/projects/) for the package workflow.
The CS50 site includes lecture videos; a paid certificate is not required to use
its public course materials.
**YouTube searches:** `CS50P functions exceptions file IO unit tests`, `Python type hints dataclasses context managers`, `uv Python pyproject lock virtual environment`.

## 7. Phase 2 — Linux, shells and permissions

**Purpose:** navigate the server, inspect it and understand why commands succeed
or fail at the OS boundary.

**Subtopics:** working directory, absolute/relative paths, home directory, `pwd`,
`ls`, `cd`, `cat`, pipes, redirects, shell variables, process environment, file
ownership and modes, `sudo`, package managers, services/systemd, logs, memory and
disk inspection. Compare Unix permissions with Windows ACLs. Understand PowerShell
syntax separately from Bash; PowerShell 5.1 does not support Bash's `&&` syntax.

**Prerequisites:** phase 0; basic files and folders.

**Exercises:** create and navigate a lab folder; inspect `pwd`, `whoami`, `df -h`,
`free -h` and a process listing; write a non-secret environment variable and read
it from Python; explain each part of `sudo systemctl status docker`. Practise
permissions on a throwaway text file, not your real SSH key.

**Project connection:** the Dockerfile-not-found error, EC2 package installation,
and the Windows key ACL failure.
**Ready to advance when:** you can identify the active machine and user, find a
file without guessing paths, and distinguish a permission error from a network error.

**Primary resource:** [MIT Missing Semester](https://missing.csail.mit.edu/) shell/tooling material.
**YouTube searches:** `MIT Missing Semester shell`, `Linux command line permissions sudo systemctl beginners`, `PowerShell vs Bash environment variables`.

## 8. Phase 3 — Git and GitHub

**Purpose:** understand how source revisions move, and how to recover and review changes.

**Subtopics:** repository, working tree, index/staging, commit, branch, HEAD,
remote/origin, push, fetch, pull, clone, diff, log, merge and basic conflicts,
`.gitignore`, reviewing changes before publication. GitHub adds hosting, pull
requests and Actions; it is not the same program as Git.

**Prerequisites:** terminal/file basics.

**Exercises:** in a disposable repo make two commits; change a file without committing
and compare `git diff` with `git diff --cached`; create a branch and merge a small
change; clone into another lab folder and compare commit ids. Add a fake secret
filename to ignore rules before creating the file, then verify it is excluded.

**Project connection:** pushed revision `3d0bd84` and the same HEAD on EC2.
**Ready to advance when:** you can tell whether a change exists only locally, in a
commit, on GitHub, or in the server checkout. Do not practise destructive Git
commands against the real project to prove this.

**Primary resource:** [Pro Git](https://git-scm.com/book/en/v2), starting with basics.
**YouTube search:** `freeCodeCamp Git and GitHub for Beginners Crash Course Gwen Faraday`.
You may use a newer beginner lesson; the official book is the command reference.

## 9. Phase 4 — Networking, HTTP and API fundamentals

**Purpose:** understand what it means for an application to listen and for a client
to call it.

**Subtopics:** IP and DNS, TCP ports, loopback/localhost, bind addresses (`127.0.0.1`
versus `0.0.0.0`), URL parts, HTTP methods/headers/body/status codes, JSON, request
timeouts, TLS/HTTPS, firewall rules, client versus server, synchronous request flow.
Distinguish SSH encryption from HTTPS: they protect different connections.

**Prerequisites:** phases 0–2.

**Exercises:** start a tiny local health API; call it from a browser and from
`Invoke-RestMethod`; change the port; deliberately request a missing route;
stop the server and observe a connection failure rather than an HTTP response.
Draw which process owns each listening port.

**Project files:** `hello/health_app`, `knowledge_api.py`, `compose.yaml`.
**Ready to advance when:** you can distinguish a refused connection, 404, 401,
403 and 503, and explain why a container port is not automatically public.

**Primary resource:** [MDN HTTP overview](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview).
**YouTube searches:** `HTTP request response headers JSON status codes beginners`, `localhost 127.0.0.1 0.0.0.0 ports explained`, `DNS TLS HTTPS reverse proxy basics`.

## 10. Phase 5 — FastAPI, Pydantic and backend architecture

**Purpose:** implement a small API whose behavior you can change and debug yourself.

**Subtopics:** routing/path operations, query/body parameters, validation models,
response models, dependency injection, exception handling, API authentication,
OpenAPI/Swagger UI, settings, separating route handlers from business logic,
HTTP clients and bounded upstream calls.

**Prerequisites:** Python and HTTP fundamentals.

**Exercises:** build a notes API in your lab: health route, create/list/get notes,
strict request validation, in-memory storage initially, and one read-protected
route. Reject an empty note and unknown fields. Add a fake downstream service and
show that its failure becomes a controlled response rather than leaking details.

**Project files:** `knowledge_api.py`, `chat.py`, `auth.py`.
**Ready to advance when:** you can add a route, validate its body, inject a test
dependency and explain what Uvicorn does separately from FastAPI.

**Primary resource:** [FastAPI tutorial](https://fastapi.tiangolo.com/tutorial/).
**Short video:** [FastAPI Course for Beginners — freeCodeCamp / Code With Tomi](https://www.youtube.com/watch?v=tLKKmouUams).
**Long reference:** [Python API Development — freeCodeCamp / Sanjeev Thiyagarajan](https://www.youtube.com/watch?v=0sOvCWFmrtA).
Use selected chapters rather than attempting the entire long course at once.
The videos are older: compare Pydantic/settings/testing examples with our installed
versions. Their ORM/JWT approach is not our raw psycopg SQL/opaque-token design.
**Search:** `FastAPI Pydantic v2 dependency injection HTTPBearer testing`.

## 11. Phase 6 — PostgreSQL, transactions and data ownership

**Purpose:** make application data persistent and maintain correct ownership.

**Subtopics:** tables/rows/columns, schema, data types, primary/composite/foreign
keys, SELECT/INSERT/UPDATE/DELETE, WHERE/JOIN/ORDER BY/LIMIT, indexes, transactions,
rollback/savepoints, upserts, parameterized SQL, connection strings, TLS, schema
initialization versus migrations, local versus hosted DB.

**Prerequisites:** basic Python/API logic. SQL can be learned alongside the notes API.

**Exercises:** store lab notes in a separate local DB; add two tenant organizations;
query only the caller's tenant; test matching document ids in both tenants; provoke
a transaction failure and show that earlier writes rolled back; safely repeat an
upsert without duplicating records. Use fake or synthetic data only.

**Project files:** `schema.sql`, `database.py`, `ingestion.py`, `bootstrap.py`.
**Ready to advance when:** you can write the tenant-filtered join, explain why a
foreign key includes a tenant, and separate the database role from the API user.

**Primary resources:** [PostgreSQL 16 tutorial](https://www.postgresql.org/docs/16/tutorial.html),
[Neon introduction](https://neon.com/docs/introduction).
**Searches:** `PostgreSQL SQL joins transactions parameterized queries Python psycopg 3`, `multi tenant database composite foreign key tenant isolation`.

## 12. Phase 7 — Testing, fakes and code quality

**Purpose:** turn requirements into checks you can rerun after changing code.

**Subtopics:** assertions, unit/integration/API/contract/smoke testing, fixtures,
parametrization, fake/stub/mock distinctions, monkeypatching, isolated databases,
transaction cleanup, deterministic tests, negative cases, linting and formatting.

**Prerequisites:** the Python functions and components you want to test.

**Exercises:** test notes validation; inject a fake model; test expired or missing
credentials; prove that tenant A cannot read tenant B's note; test a DB rollback;
intentionally introduce an ownership bug and confirm the isolation test catches it.
Do not send real hosted inference requests in every unit test.

**Project files:** `tests/conftest.py`, `test_database.py`, `test_knowledge_api.py`,
`test_answering.py`. Read setup, action and assertion separately.
**Ready to advance when:** you can explain what a test proves, what it leaves
unproven and why a skipped integration test is not a passing integration test.

**Primary resource:** [pytest getting started](https://docs.pytest.org/en/stable/getting-started.html).
**Searches:** `pytest fixtures parametrization monkeypatch tutorial`, `FastAPI TestClient dependency overrides`, `Ruff lint vs format`.

## 13. Phase 8 — Docker and Compose

**Purpose:** package and run your lab API without reconstructing its environment by hand.

**Subtopics:** image/container/registry, Docker daemon/client, base images/layers,
build context, COPY/RUN/CMD, WORKDIR/ENV/USER/EXPOSE, image tags and digests,
multi-stage builds, non-root containers, port publishing, container DNS, volumes,
Compose services/networks, environment injection, logs, exit codes, restart policies,
BuildKit/buildx. Learn the simple lifecycle before build-cache optimization.

**Prerequisites:** shell, ports and a working local API.

**Exercises:** write a small Dockerfile for the notes API; build it, list the image,
start a container and call health; stop it and observe the failure; inspect logs;
run a local DB alongside it in Compose; recreate a container while retaining DB data
in a lab volume. Deliberately use the wrong build directory once and diagnose it.

**Project files:** service Dockerfile, `.dockerignore`, `compose.yaml`.
**Ready to advance when:** you can explain why build does not start the API, why
EXPOSE does not publish a port, and which data survives container replacement.

**Primary resource:** [Docker getting started](https://docs.docker.com/get-started/).
**Video:** [Docker Crash Course for Absolute Beginners — TechWorld with Nana](https://www.youtube.com/watch?v=pg19Z8LL06w).
**Longer alternative:** [Docker Tutorial for Beginners — TechWorld with Nana](https://www.youtube.com/watch?v=3c-iBn73dDE).
Use conceptual chapters and adapt the example language to Python. Old videos may
use `docker-compose`; this project uses `docker compose`. Paid registry/cloud
examples are optional, not a reason to spend money.
**Search:** `Docker Python FastAPI multi stage Docker Compose volumes networking`.

## 14. Phase 9 — CI/CD and GitHub Actions

**Purpose:** understand and eventually modify the green-check workflow yourself.

**Subtopics in order:**

1. Git events, YAML mappings/lists/indentation and nonzero exit codes.
2. Workflows, runs, jobs, runners, steps, `uses` versus `run`.
3. Checking out source; setting up Python and installing locked dependencies.
4. Lint, format and test commands; reading logs and failing steps.
5. Service containers, health checks and environment variables for integration tests.
6. Permissions and least privilege; action version pinning; secrets versus public test settings.
7. Dependency caches versus release artifacts; image registries, tags and immutable digests.
8. Branch protection and required checks; these require configuration beyond a workflow.
9. Delivery/release approval, deployment environments, smoke tests and rollback.
10. Later: short-lived cloud identity/OIDC, concurrency, matrix testing and artifact promotion.

**Prerequisites:** Git, Python tests, basic shell; Docker for understanding our final step.

**Exercises:**

1. In a lab repository, run one test on push. Intentionally fail and repair it.
2. Add Ruff checks; distinguish a style failure from a failing assertion.
3. Add a temporary local DB service and a small integration test without cloud secrets.
4. Build the notes image. Explain where it exists after the job and why the server
   still has no new running container.
5. Design a release flow on paper: passing revision -> image artifact -> approval
   -> deploy -> smoke check -> rollback. Implement automation later, with current
   cloud permissions and free limits reviewed first.

**Project connection:** our `checks` workflow and the passed run for `3d0bd84`.
**Ready to advance when:** you can identify the exact failing step, rerun its command
locally, and describe which deployment operations the workflow does not perform.

**Primary resource:** [GitHub Actions concepts](https://docs.github.com/en/actions/get-started/understand-github-actions).
**Video reference:** the long [Python API Development course](https://www.youtube.com/watch?v=0sOvCWFmrtA)
has CI/CD and GitHub Actions chapters; search within its chapter list.
**YouTube searches:** `GitHub Actions tutorial beginners Python pytest service containers`,
`TechWorld with Nana GitHub Actions basic concepts CI CD Docker`,
`continuous integration continuous delivery continuous deployment differences`.
Use current action versions from official documentation; do not copy obsolete pins
or put long-lived AWS keys into a workflow just because an old lesson does so.

## 15. Phase 10 — AWS deployment and operations

**Purpose:** understand the server we prepared and make a deployment operable.

**Subtopics:** cloud/virtual machines, AWS Regions and Availability Zones, EC2/AMI/
instance type, EBS/gp3, VPC/subnets, public/private IPs, security groups, SSH keys
and host fingerprints, Windows ACLs, IAM users/roles/policies/MFA, Free-plan credits,
secrets management/Parameter Store, TLS/reverse proxies, startup/restart policies,
log rotation, memory/disk monitoring, release revisions and rollback. Understand
that stopping compute leaves persistent resources such as EBS storage.

**Prerequisites:** Linux, networking, Git, Docker and a tested application.

**Exercises:**

1. Reconstruct the already-performed EC2 choices on paper and explain each one.
2. Draw SSH from your IP to port 22 and distinguish that from an HTTPS API request.
3. Inspect Docker status, disk, memory and logs on an authorized server without
   displaying environment secrets.
4. Practise a container restart and rollback on the lab laptop before the cloud service.
5. When the approved deployment is ready, verify health, readiness, authentication,
   tenant behavior and a real answer over HTTPS, then save an evidence artifact.

**Project references:** [AWS deployment notes](deploy-aws.md),
[fallback notes](deploy-render.md). EC2 and its image exist; cloud API runtime and
public smoke test are still pending. Do not create more servers to follow lessons.

**Ready to advance when:** you can distinguish VM status from API readiness, explain
where secrets/data live and safely recover the tested application after a restart.

**Primary resources:** [EC2 concepts](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html),
[AWS Free Tier FAQ](https://aws.amazon.com/free/free-tier-faqs/).
**YouTube searches:** `AWS EC2 Ubuntu SSH security groups beginner Amazon Web Services`,
`AWS IAM roles least privilege MFA beginner`, `Docker FastAPI deployment HTTPS reverse proxy`,
`AWS Systems Manager Parameter Store SecureString instance role`.
Cloud interfaces and eligibility change. Verify live account options rather than
treating a tutorial's old free-tier claim as a spending guarantee. Never upgrade
or provision paid services for these exercises.

## 16. Phase 11 — Embeddings, semantic search and RAG

**Purpose:** understand the core AI feature rather than treating retrieval as magic.

**Subtopics:** pretrained inference versus training, tokens versus characters,
embeddings/vectors/dimension, cosine similarity/distance, chunking/overlap, metadata,
title prefixes, query/document embedding paths, pgvector, exact nearest-neighbor
search, top-k, threshold calibration, context construction, structured model output,
citations, abstention and prompt injection as untrusted-data handling. Approximate
indexes, hybrid search and reranking come after the baseline is understood.

**Prerequisites:** Python, SQL, HTTP and basic vectors/dot products. You do not need
to train a transformer before implementing this application.

**Exercises:**

1. Compare cosine similarity between a few toy vectors by hand and with Python.
2. Split one small article into overlapping windows and inspect exact boundaries.
3. Embed five small policies and three questions with the same model; inspect rankings.
4. Store/search those vectors in a local pgvector database with mandatory tenant filters.
5. Ask for evidence in retrieved text; reject a fabricated quote and a real quote
   from the wrong tenant.
6. Compare a policy question with a concrete order-status question and explain
   why retrieval of related policy text does not establish the order fact.

**Project files:** `chunking.py`, `embeddings.py`, `database.py`, `answering.py`,
`chat.py`, `data/` and `evals/retrieval/`.
**Ready to advance when:** you can trace one article through ingestion and one
question through retrieval/answering, including failure/refusal paths.

**Primary resources:** [FastEmbed](https://qdrant.github.io/fastembed/),
[pgvector](https://github.com/pgvector/pgvector). The source implements exact
tenant-filtered retrieval; installing pgvector does not automatically create a
high-quality approximate index or solve tenant security.
**Searches:** `RAG explained embeddings chunking retrieval citations`,
`cosine similarity semantic search Python`, `pgvector PostgreSQL cosine distance tutorial`,
`Qdrant FastEmbed BGE query embeddings`.

## 17. Phase 12 — AI evaluation and observability

**Purpose:** measure whether the AI feature is useful, and locate failures.

**Subtopics:** labelled datasets, answerable/unanswerable cases, Recall@k/MRR,
multiple relevant documents, citation provenance versus relevance, answer faithfulness,
refusal precision/recall, tuning versus held-out evaluation, reproducibility,
error categories, latency and token usage, logs, request ids, traces/spans, redaction.

**Prerequisites:** retrieval and testing.

**Exercises:** create ten independently reviewed small questions, keeping some
aside while tuning; manually compute ranks/MRR; compare two chunk settings; inspect
false acceptances and false refusals; trace one failed retrieval/model call using
synthetic data; check that credentials and sensitive prompts are not logged.

**Project evidence:** Day 3 experiments and Day 4 smoke artifact. Our synthetic
in-sample Recall@5 of 1.000 is not a general production-quality result. One real
cited answer is not a full answer benchmark. Langfuse setup trace exists; complete
agent tracing is not yet implemented.
**Ready to advance when:** you can report a result with dataset size, settings,
method and limitations, and use a trace/log to narrow down an observed failure.

**Primary resources:** [Langfuse observability](https://langfuse.com/docs/observability/overview),
our [retrieval methodology](../evals/retrieval/README.md), and the evaluation material
in the [Hugging Face Agents Course](https://huggingface.co/learn/agents-course/en/unit0/introduction).
**Searches:** `Recall at k MRR information retrieval evaluation`, `RAG evaluation faithfulness answer relevance`,
`Langfuse tracing Python tutorial`.

## 18. Phase 13 — Tool calling and bounded agent loops

**Purpose:** understand how an application executes a model-requested action.

**Subtopics:** model messages, tool schemas, validated arguments, tool-call ids,
dispatch/allowlists, tool results, loop state, stopping conditions, timeouts,
step/token limits, provider adapters, deterministic policy checks, side effects,
idempotency and escalation. A model requesting a tool does not execute it by itself.

**Prerequisites:** Python/API/JSON, testing and basic RAG.

**Exercises:** implement a fake order lookup on synthetic records; let a scripted
fake model request it; dispatch only allowed tools; reject invalid arguments and
cross-tenant orders; enforce a small step limit; compare local and hosted model
requests without allowing real financial operations.

**Project status:** an early simple Ollama tool-call experiment exists; a complete
support loop and mock backend do not. Follow the PRD's Day 6–7 requirements after
the Knowledge API gate work, including scenarios and deterministic policy tests.
**Ready to advance when:** you can write the loop, enforce boundaries outside the
model and explain why a tool result is data rather than a trusted instruction.

**Primary resource:** [Hugging Face AI Agents Course](https://huggingface.co/learn/agents-course/en/unit0/introduction).
**Searches:** `LLM tool calling agent loop from scratch Python`, `Hugging Face agents course tools observations actions`,
`tool calling schema validation step limits Python`.
Treat provider-specific function-call syntax as version-sensitive.

## 19. Phase 14 — LangGraph, persistence and human approval

**Purpose:** represent a controlled workflow and preserve it across pauses/restarts.

**Subtopics:** state schema, nodes, edges, conditional routing, reducers, graph
execution limits, checkpointers/thread identities, durable state, interrupts/resume,
approval identity/record, rejection, replay/idempotency, deterministic policy checks,
mock refunds, trace spans and failure escalation.

**Prerequisites:** bounded tool loop, SQL/transactions and tests.

**Exercises:** draw the support graph before coding; test every route with a fake
model; pause a fictional refund for approval; kill/restart the lab process; reject
one run and approve another; prove no execution occurs without the required
approval and no duplicate refund is recorded on retry. Begin with SQLite locally,
then use the PRD's Postgres persistence path for deployment.

**Project status:** planned. Target nodes include intake, retrieval, lookup,
planning, policy check, approval, execution, reply and escalation. The refund
approval requirement is mandatory regardless of the model's confidence.
**Ready to advance when:** restart/resume and rejection work in tests, and the
execution path cannot bypass the code-enforced approval policy.

**Primary resources:** [Introduction to LangGraph course](https://academy.langchain.com/courses/intro-to-langgraph),
[current LangGraph documentation](https://docs.langchain.com/oss/python/langgraph/overview).
Some Academy examples use older APIs or optional hosted products; adapt them to
installed versions and use free local labs.
**Searches:** `LangGraph state nodes conditional edges Python`, `LangGraph interrupt resume checkpointer human in the loop`,
`idempotent side effects approval workflow agents`.

## 20. Phase 15 — MCP and secure multi-tenant tools

**Purpose:** expose existing application capabilities through an interoperable protocol.

**Subtopics:** MCP host/client/server roles, tool discovery/calling, tools versus
resources/prompts, schemas, stdio versus Streamable HTTP, session/lifecycle behavior,
Inspector, bearer authentication, scopes, expiry/revocation, ownership checks,
generic errors, indirect prompt injection and least-privilege downstream access.
Learn modern MCP authorization requirements separately; our initial scoped-token
demo does not imply full OAuth interoperability or protocol-security completeness.

**Prerequisites:** HTTP APIs, tool dispatch, schemas, authentication/authorization,
testing and tenant-aware database access.

**Exercises:** register a harmless read-only tool over stdio and call it from
Inspector; add schema validation; build an isolation table of missing/wrong/expired/
revoked credentials and foreign record ids; expose read-only tools over the planned
HTTP transport; replace a direct agent tool with an MCP call and compare results.
Keep refund execution outside the read-only MCP surface.

**Project status:** planned. Do not report zero MCP leaks before implementing and
running its tests. The Knowledge API's tenant tests do not establish MCP isolation.
**Ready to advance when:** every exposed surface enforces its scope and tenant,
and agent evaluation does not materially regress when using MCP tools.

**Primary resources:** [MCP introduction](https://modelcontextprotocol.io/docs/getting-started/intro),
[Hugging Face MCP Course](https://huggingface.co/learn/mcp-course/en/unit0/introduction).
**Searches:** `Model Context Protocol host client server tools resources prompts`,
`MCP Python SDK stdio Streamable HTTP Inspector tutorial`, `MCP authorization tenant isolation security`.
Check the current specification and installed SDK before copying registration or transport APIs.

## 21. Phase 16 — Finish, verify and explain

**Purpose:** turn components into an understandable, reproducible project with honest evidence.

**Subtopics:** end-to-end verification, release revisions, clean-clone setup,
documentation, architecture decisions, regression datasets, operational limits,
demo preparation and communicating personal contributions.

**Prerequisites:** the relevant earlier phases and the implemented PRD features.

**Exercises:** have someone follow the README in a fresh folder; verify ticket ->
tool lookup -> policy -> approval -> recorded fictional action -> reply; compare
agent results before/after MCP; review secrets and account resources; rehearse a
walkthrough that includes one real failure and how evidence narrowed its cause.

**Evidence to collect:** real test/eval totals, settings and datasets; public smoke
results only after deployment; actual approval tests; actual MCP isolation results;
a short demo and accurate limitations. State what was assistant-implemented and
what you independently rebuilt or debugged. Independent skill claims should follow
practice, not the existence of generated files.

**Ready to finish when:** the PRD gates and intended features are verified, the
instructions work for a fresh user and you can explain the architecture and a
small code change using references as needed. Not all gates are complete today.

## 22. A single smaller project to practise through the phases

Use a **two-tenant notes assistant** as the lab project. Grow it only when the
previous stage is understandable:

```text
Read/write a local text file
        ↓
Python notes module + a few tests
        ↓
FastAPI notes routes + validation
        ↓
Postgres storage + tenant filters
        ↓
Dockerfile + Compose
        ↓
GitHub CI: lint, tests and image build
        ↓
Optional deployment after local practice
        ↓
Semantic search across notes + source citations
        ↓
Bounded read-only tool loop
        ↓
Durable human-approved fictional action
        ↓
Read-only MCP tools
```

This is smaller than reproducing the entire support platform at once. You can
revisit Support Copilot's equivalent files after implementing each lab feature.
Do not add unrelated frameworks simply because a tutorial uses them.

## 23. Video and resource selection guide

Resources were looked up on 23 October 2026. Links and course access can change.
The direct video links below were found on their publisher/creator listings;
they are recommended for concepts, not as an endorsement of every old command.
No paid course or certificate is required by this roadmap.

| Need | Start here | Then consult |
|---|---|---|
| Python foundation | CS50P lecture material | Your small module and Python errors |
| Shell/tool confidence | MIT Missing Semester | The server's help/man pages |
| Git | One focused beginner lesson + lab commits | Pro Git |
| Short FastAPI introduction | freeCodeCamp / Code With Tomi video | Current FastAPI tutorial |
| Longer backend reference | freeCodeCamp / Sanjeev Thiyagarajan course | Selected chapters, adapted to installed versions |
| Docker concepts | Nana crash course | Current Docker docs and actual Dockerfile |
| CI | Tiny lab workflow, then GitHub Actions docs | Real `ci.yml` and failed-step logs |
| AWS | EC2 concepts and narrow official video searches | Actual Free-plan console options |
| RAG | Small vector-search exercise | FastEmbed + pgvector docs |
| Agents | Hugging Face Agents Course | A bounded fake-model loop |
| Graphs/approval | LangGraph Academy and current docs | Fake-based restart/approval tests |
| MCP | Hugging Face MCP Course | Current protocol and SDK docs |

The 2021 long backend course's publisher lists chapters on FastAPI, SQL, testing,
Docker and CI/CD. It is useful as a reference, but historical Heroku/free-tier,
Pydantic, authentication and deployment commands need current verification. We
are not adopting its full architecture or requiring its entire duration.

When choosing additional YouTube material, prefer a lesson with visible working
examples, source code and exercises. Check dates and installed versions. Watch
one instructor per topic initially; switching among ten playlists usually adds
terminology faster than understanding. Skip upsells and paid infrastructure labs.

## 24. Optional study tracker

Fill this after practice; nothing is pre-marked as mastered.

| Topic | Read/watched | Rebuilt a small version | Changed a requirement | Debugged a failure | Evidence/note |
|---|---|---|---|---|---|
| Execution environments | | | | | |
| Python + uv | | | | | |
| Linux and permissions | | | | | |
| Git | | | | | |
| HTTP/FastAPI | | | | | |
| SQL/transactions | | | | | |
| Testing/Ruff | | | | | |
| Docker/Compose | | | | | |
| CI/GitHub Actions | | | | | |
| AWS/operations | | | | | |
| RAG/retrieval | | | | | |
| Evals/tracing | | | | | |
| Tool loop | | | | | |
| LangGraph/approval | | | | | |
| MCP/security | | | | | |

**Your first step:** read walkthrough sections 1–4 and 10, then do the first tiny
Git/CI lab. You can return to the rest of the roadmap one phase at a time. The
deployment task remains paused at Neon inspection until you choose to resume it.
