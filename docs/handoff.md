# Handoff: project state as of 19 October 2026

## Latest update on 23 October 2026

**This update supersedes the historical status and next-step statements below.**

- Workflow: the user explicitly authorized the assistant to implement core code,
  Dockerfiles and tests and chose to study afterward. The matching override is in
  both AGENTS.md and CLAUDE.md. Do not require quizzes, predictions, manual coding
  or an explain-back before implementation. Do not claim learning checks passed.
- Day 0 technical checks are complete: Docker `/health` was verified; the user
  confirmed the Langfuse trace input/output; the user reported Neon vector 0.8.6.
  AWS is still deferred to deployment, and commits/pushes remain with the user.
  The original full Gate G0 is not claimed because learning checks/AWS were deferred.
- Day 1 database foundation is implemented in `src/support_copilot`: settings,
  lazy FastEmbed adapter, schema, safe document replacement and tenant-filtered
  raw SQL nearest-neighbor retrieval. `compose.yaml` runs local Postgres with pgvector.
- `pyproject.toml` and `uv.lock` exist. Use `uv add` for dependency changes and
  `uv sync --frozen --cache-dir G:\uv-cache` for installation. Locked runtime versions
  include psycopg 3.3.6, pgvector 0.5.1 and fastembed 0.9.0.
- Verification: 26 tests passed against the real local `copilot_test` database and
  fake-based unit tests. Five real-embedding questions ranked the expected article
  first in a three-document corpus. Saved results: `evals/results/day-01-search.json`.
  This is not a full retrieval benchmark. Local pgvector is 0.8.7.
- README now documents local commands, limitations and tests. Day 0/1 journals
  record technical evidence without claiming the user independently learned it.
- The local DB is loopback-only with public demo credentials, separate from Neon.
  No existing .env values were copied or printed, and no cloud DB data was changed.
- Day 2 is implemented: 15 Northwind articles, 3 Contoso isolation fixtures,
  deterministic character chunking and trusted-admin Markdown ingestion. The
  default 800/120 size/overlap yields 30 Northwind and 6 Contoso chunks. See data/README.md.
- Verification now totals **64 passing tests**, including real Postgres ingestion,
  batch rollback, re-ingest idempotency and tenant-isolation cases. Two real imports
  produced identical source text hashes, ids and counts; evidence is saved in
  `evals/results/day-02-ingestion.json`.
- The Day 1 search demo now uses `northwind-day1-demo`, keeping it separate from
  the full corpus so rerunning it does not replace help articles.
- Day 3 is complete: `evals/retrieval/questions.jsonl` has 40 answerable and 10
  unanswerable synthetic questions. Five configurations were evaluated with the
  actual model/database. Recall@5 was 1.000 for all; MRR@5 improved from baseline
  0.950 to 1.000 for 1200-character chunks. These are in-sample assistant-authored
  development fixtures, not independently reviewed or held-out evaluations.
- Evidence: `evals/results/day-03-retrieval.json` and the readable Markdown summary.
  Metrics and rounded ranks/scores matched on a full independent rerun. Experiments
  rolled back their temporary tenants and preserved the original 30/6 chunk counts.
- The larger-chunk calibrated score gate rejected 9/10 unanswerable questions but
  also rejected 5/40 answerable questions. q047 (actual refund approval date) still
  passed despite absent evidence. The zero-overlap setting had a better gate balance
  (95% answerable acceptance, 90% unanswerable rejection). Score gates are not proof
  of answer correctness or LLM refusal. See evals/retrieval/README.md.
- Verification now totals **91 passing tests**; lint and formatting are clean.
- Importer defaults remain 800/120. Choose API operating settings based on both
  retrieval and answer/refusal measurements, rather than silently changing the corpus.
- Day 4 Knowledge API now works locally in Docker: `/health`, `/ready`, scoped
  `/v1/search`, `/v1/ask` and `/v1/ingest`. Tokens bind a caller to one tenant;
  only hashes are stored in Postgres. Provisioned NORTHWIND_API_TOKEN (read/write)
  and CONTOSO_API_TOKEN (read) into the ignored .env without printing their values.
- Answers are validated source quotations with citations, not arbitrary generated
  prose. Unknown/invalid evidence is refused. Concrete order references return
  `record_lookup_required` because orders are not in the KB. Provenance validation
  does not prove relevance or completeness; no held-out answer benchmark is claimed.
- Verification now totals **143 passing tests**. Docker image built and service is
  healthy at http://localhost:8001; interactive docs: http://localhost:8001/docs.
  A real Groq `openai/gpt-oss-20b` request returned the verified one-year warranty
  quote. Smoke checks also verified both tenants, missing-token rejection and
  order-specific refusal. Evidence: `evals/results/day-04-api-smoke.json`.
- Current container uses temporary PowerShell hosted-model overrides because only
  about 0.5 GB RAM was free. Existing .env still defaults to Ollama. Reapply the
  hosted startup commands in `services/knowledge-api/README.md` before recreating
  it in a new terminal. Do not load the local model while memory is constrained.
- Docker startup seeds only empty corpora and preserves operator edits. The image
  excludes .env and runs unprivileged. CI is configured but has not run on GitHub;
  it will run after the user pushes. No assistant commit/push was made.
- Day 5 deployment preparation exists: `docs/deploy-aws.md`, `render.yaml`
  (optional explicitly Free fallback, auto-deploys off), `docs/deploy-render.md`
  and `docs/journal/day-05.md`. No AWS CLI/profile/credentials or Render API key
  were found. AWS account status was requested from the user. Official hosting
  docs were checked; account-specific free eligibility remains to be established.
- On 23 October the user confirmed the AWS Free plan by screenshot: $100 credit,
  $0 current spend, expiry 14 April 2027 (or earlier if credits run out). The user
  launched one Ubuntu Server 24.04 LTS x86 EC2 t3.small with 20 GiB gp3 in Sydney
  (ap-southeast-2), with SSH restricted to My IP; HTTP/HTTPS inbound are closed.
  Screenshot showed 3/3 checks passed. Public IP at launch: 13.210.138.248.
- User connected over SSH as ubuntu. A Windows key ACL error was fixed by granting
  the user's read access, removing inherited access and CodexSandboxUsers access.
  The private .pem remains outside the repo; *.pem and *.key are now git-ignored.
- User-provided server output confirms Docker hello-world success and Compose
  2.40.3 after installing Ubuntu docker.io, docker-compose-v2 and git. This is
  server preparation, not a running cloud Knowledge API. AWS compute/storage
  consume credits; account expiry is not a promise credits last until then.
- User committed/pushed `3d0bd84`. The user's GitHub screenshot confirms the
  `checks` workflow passed for that commit. User then cloned it onto EC2 and
  verified HEAD. The service Docker image built successfully there as
  `support-copilot-knowledge:3d0bd84`, image id `04d288243eea`; build output supplied
  by user. Legacy-builder warning did not prevent success. The application has
  not been started on EC2 and no public HTTPS answer has been verified.
- On the user's request, added `docs/PROJECT_EXPLAINED.md` (complete explanatory
  walkthrough) and `docs/LEARNING_ROADMAP.md` (phases, prerequisites, exercises,
  official resources and video links/search terms). User expressed confusion and
  wanted understanding; this is a documentation/study detour, not revocation of
  the implementation-first override. Learning checks remain deferred.
- Neon inspection confirmed neondb, vector 0.8.6 and initially no public tables.
  The user's init-db attempt created the schema but failed on the second connection:
  Neon pooling rejects statement_timeout in connection startup options. Fixed
  database.connect() to SET LOCAL statement_timeout = '10s' in its transaction.
  Added a real-Postgres regression covering pooler compatibility, timeout and recovery.
  All **144 tests passed**; lint/format passed. See docs/debug-log.md entry 3.
- Assistant reran the already-authorized Neon initialization successfully using
  the tested fix. Actual output: ready, vector 0.8.6, dimension 384; read-back shows
  2 tenant records, 0 documents and query timeout 10s. No secrets were printed or
  copied into another file. .env values were not changed.
- User then supplied successful Neon seed results: Northwind 15 documents/30 chunks,
  Contoso 3 documents/6 chunks, BGE small model, 800/120 character settings.
  User also supplied successful token provisioning: NORTHWIND_API_TOKEN has
  kb:read/kb:write; CONTOSO_API_TOKEN has kb:read. Hashes registered in Neon;
  credential values were not displayed. Public API testing remains pending.
- **Exact next operational step:** user commits/pushes the connection fix and
  documentation, obtains passing CI, then updates/rebuilds the EC2 image: 3d0bd84
  contains the old incompatible startup option. Then configure runtime secrets
  and HTTPS before public authenticated smoke tests. Agent/MCP, Day 5 completion
  and Gate G1 remain pending.
- No commit or push was made by the assistant.

The remainder preserves the 19 October handoff for historical context.

Written for the next coding agent (Codex) taking over from Claude Code. Read [AGENTS.md](../AGENTS.md) first for the rules and teaching style. This file is the state: what exists, what was decided, what was learned, and what to do next.

## 1. Where the project is

- **PRD day:** still **Day 0** (setup and foundations). Gate G0 has not passed yet.
- **Calendar:** the PRD plan started Sun 11 Oct 2026, so by the calendar it would be Day 8. The learner chose to delay the schedule rather than skip setup. The PRD's Day 7 catch-up and its cut line (Section 13.4) will be needed later; plan to re-baseline the dates with the learner once Day 1 starts.
- **Remaining for Gate G0:** the Docker hello-world check (built, not yet run), the Langfuse test trace, the Day 0 journal entry, and a commit.

## 2. The machine

| Item | Value |
|---|---|
| OS | Windows 11 Home Single Language (build 26200) |
| RAM | 7.8 GB total; typically 0.6 to 0.9 GB free |
| GPU | NVIDIA RTX 3050, 4 GB (4,096 MiB) |
| C: | about 12 to 15 GB free (tight) |
| G: | about 53 GB free (project and large data live here) |
| D: | about 7 GB free (unused) |
| Shell | Windows PowerShell 5.1 inside VS Code |

Programs taking notable RAM besides the model: VS Code (0.7 GB), ChatGPT desktop app (0.5 GB), Brave (0.5 GB), Claude app (0.4 GB), Wispr Flow (0.3 GB). Closing the ChatGPT app and Wispr Flow frees about 1 GB when running the model.

## 3. Installed tools

| Tool | Version | Location / notes |
|---|---|---|
| Git | 2.49.0 | Default branch `main` |
| VS Code | installed | |
| Python (system) | 3.11.9 | Not used for the project |
| uv | 0.13.0 | `C:\Users\ASUS_\.local\bin` |
| Project Python | 3.12.15 | In `G:\support-copilot\.venv`, created by `uv venv --python 3.12` |
| Node.js | installed | For the MCP Inspector (Day 11) |
| WSL2 | 3.0.3, kernel 6.18 | Ubuntu installed, user `tarif_420`. Memory cap in `C:\Users\ASUS_\.wslconfig`: `[wsl2]` / `memory=3GB` |
| Docker Desktop | 4.95.0 (CLI 29.8.2) | Disk image moved to `G:\docker-data`. **Not running at last check**; the learner must start it from the Start menu |
| Ollama | 0.40.3 | Installed to `G:\Ollama`. User env var `OLLAMA_MODELS=G:\ollama-models` |
| qwen3:4b | 2.5 GB | Stored in `G:\ollama-models` |
| fastembed | 0.9.0 | In `.venv`. Model cache: `G:\fastembed-cache` |
| FastAPI / Uvicorn | 0.143.3 / 0.54.0 | In `.venv` |

Packages in `.venv` were installed with `uv pip install`; there is no `pyproject.toml` or lock file yet. The PRD's Sprint 1 recipe (Section 9.2, step 1) creates one.

## 4. Accounts

| Service | State |
|---|---|
| GitHub | Repo `Tarif205/support-copilot`, public, two commits pushed |
| Neon | Project `gentle-cell-18318154`, Free plan, region AWS US East 2 (Ohio). The learner was told to run `CREATE EXTENSION IF NOT EXISTS vector;`; **not confirmed** that it was run |
| Langfuse | Hobby account and project created; keys in `.env`. **No test trace sent yet** (Gate G0 item) |
| Groq | Account and API key created; key in `.env` as `LLM_API_KEY` |
| AWS | **Deferred to Day 5.** The learner has no money. Rule agreed: try sign-up then; if it asks for a card, stop and use the PRD's fallback (Section 15.3: Render + Neon) |

## 5. The `.env` file (names only, never print values)

```
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=qwen3:4b
EMBED_PROVIDER=fastembed
EMBED_MODEL=BAAI/bge-small-en-v1.5
DATABASE_URL=            (empty until Day 1 local Postgres)
LANGFUSE_SECRET_KEY      (set)
LANGFUSE_PUBLIC_KEY      (set)
LANGFUSE_BASE_URL        (set, Langfuse cloud URL)
LLM_API_KEY              (set, Groq key)
NEON_DATABASE_URL        (set; for deployment on Day 5, not read by code)
```

Values were unquoted on purpose: `docker run --env-file` keeps quotes as part of the value. `LLM_API_KEY`, `DATABASE_URL` and `NEON_DATABASE_URL` are names chosen in this project, not fixed by the PRD. `.env.example` lists the non-secret names; it does not yet list the Langfuse names or `NEON_DATABASE_URL`. Add them (empty values) when the code first reads them.

## 6. Files in the repository and why each exists

| Path | Purpose | Git state |
|---|---|---|
| `README.md` | Skeleton: service table, layout, empty results table | Committed |
| `.gitignore` | Ignores `.env`, `.venv/`, caches, SQLite files | Committed |
| `.env.example` | Setting names with safe defaults, no secrets | Committed |
| `CLAUDE.md` | The learning contract (for Claude Code) | Committed; **modified** (rule 8 changed to allow reading `.env`) |
| `AGENTS.md` | Same contract plus teaching notes (for Codex) | New, uncommitted |
| `docs/handoff.md` | This file | New, uncommitted |
| `docs/git-commands.md` | Git command reference tables the learner asked for | Committed |
| `docs/debug-log.md` | Template only; no entries yet | Committed |
| `docs/journal/day-00.md` | Journal template, **still blank** | Committed |
| `hello/embed_check.py` | Day 0 check 2: embeddings + cosine similarity | Uncommitted |
| `hello/tool_call_check.py` | Day 0 check 3: raw tool-call request to Ollama | Uncommitted |
| `hello/health_app/main.py` | Day 0 check 1: FastAPI app with `GET /health`. The learner typed it | Uncommitted |
| `hello/health_app/requirements.txt` | `fastapi==0.143.3`, `uvicorn==0.54.0` | Uncommitted |
| `hello/health_app/Dockerfile` | `python:3.12-slim`, copy requirements, install, copy code, `CMD uvicorn ... --host 0.0.0.0 --port 8000`. Written by the assistant at the learner's explicit request, with a comment on every line | Uncommitted |
| `services/*`, `evals/*`, `data/`, `infra/`, `.github/workflows/` | Empty PRD layout (Section 4.6), held by `.gitkeep` files | Committed |
| `Support_Copilot_PRD.md` / `.docx` | The PRD. The contract says "see docs/ for the PRD", but the files are in the root; the learner has not decided whether to move them | Committed |

`hello/` is not in the PRD layout. It holds throwaway Day 0 checks, kept apart from `services/`.

## 7. Day 0 checklist (PRD Section 5.3 and Gate G0)

| Item | State |
|---|---|
| Git, VS Code, Python 3.12, uv | Done |
| WSL2 + Ubuntu + `.wslconfig` 3 GB cap | Done |
| Docker, `docker run hello-world` | Done |
| Ollama, `qwen3:4b` pulled | Done |
| GitHub repo + layout + README | Done |
| Neon project + `vector` extension | Project done; extension not confirmed |
| Langfuse account | Done |
| Langfuse receives one test trace | **Not done** |
| Hosted model account (Groq) | Done |
| AWS free plan + alert + non-root user | Deferred to Day 5 (agreed) |
| Node.js | Done |
| Check 1: FastAPI `/health` in Docker | **Runs locally (Part A done); Docker build/run (Part B) not yet done** |
| Check 2: embedding similarity | Done |
| Check 3: local model tool call, failure noted | Done |
| Free RAM with model loaded noted | Measured (0.6 GB); not yet written in the journal |
| First journal entry | **Not done** |
| "State the project in three sentences" | Not checked |

## 8. Measurements and findings (for the journal and later decisions)

**Embedding check (`hello/embed_check.py`, bge-small-en-v1.5 via fastembed):**

| Score | Pair |
|---|---|
| 0.740 | "How do I return an item?" vs "What is your refund policy?" |
| 0.457 | "How do I return an item?" vs "The weather is sunny today." |
| 0.418 | "What is your refund policy?" vs "The weather is sunny today." |

Vectors have 384 dimensions. Unrelated pairs score about 0.4, not near 0: this model compresses its range. Consequence for Day 4: the "not found" threshold in `/v1/ask` must be chosen by measuring on the eval set, not guessed. fastembed downloaded a quantized model (67 MB, folder `models--Qdrant--bge-small-en-v1.5-onnx-Q`), not the 130 MB the PRD estimated.

**Tool-call check (`hello/tool_call_check.py`, qwen3:4b via Ollama `/api/chat`):** run twice by the assistant and twice by the learner, identical results.
- "Status of order 1042?": correct tool request every time, `get_order_status({"order_id": "1042"})`.
- "Capital of France?": correctly no tool request every time.
- **Failure:** the request sends `"think": false`, yet the model's reasoning ("Okay, the user is asking...") leaks into the text reply every time, sometimes ending with a stray `</think>`. This matters for customer-facing replies on Day 10, and supports using a hosted model for the agent.
- Only one simple tool was tested; multi-tool, multi-step behaviour is untested (Day 6).
- Ollama 0.40.3 reply shape confirmed: `message.content`, `message.tool_calls[i].function.name`, `message.tool_calls[i].function.arguments` (an object, not a string), plus `id`.

**Model resource use:** `ollama ps` showed 3.5 GB loaded with context 4096, split **33% CPU / 67% GPU**; the GPU had 3,473 of 4,096 MiB in use. Free RAM with the model loaded: **0.6 GB**. The model does not fully fit on the GPU.

**FastAPI local run (Part A):** `uvicorn main:app --port 8000` served `GET /health` with 200 OK. The browser also requested `/favicon.ico` (404), which was used to explain 404s and the visitor's random source port (4522).

## 9. Decisions made

| Decision | Reason |
|---|---|
| Use `uv`, environment named `.venv` | PRD's first choice; installs Python 3.12; `.gitignore` covers `.venv/` |
| Deleted the first environment `venv` (Python 3.11) | Wrong Python version and not git-ignored |
| Installed Ubuntu on WSL2 | Learner chose to follow the PRD checklist (about 1.5 to 2 GB) |
| Docker data, Ollama, models, fastembed cache on G: | C: is short on space |
| AWS deferred to Day 5; never enter a card | Learner has no money; PRD fallback is Render + Neon |
| Neon string stored as `NEON_DATABASE_URL`, not `DATABASE_URL` | Day 1 code uses local Postgres |
| Contract rule 8 changed: agent may read `.env`, never print values | Learner's explicit decision |
| Day 0 checks live in `hello/` | Keep throwaway checks out of `services/` |

## 10. Problems hit and how they were solved

These are real bugs worth entries in `docs/debug-log.md`; the learner has not logged any yet.

1. **Wrong venv name and Python version:** `python -m venv venv` with system Python 3.11; `.gitignore` only ignored `.venv/`. Fixed by deleting it and running `uv venv --python 3.12`.
2. **VS Code kept activating the deleted `venv`:** fixed via Python: Select Interpreter → `.venv`.
3. **`wsl --install` installed WSL but no distribution:** fixed with `wsl --install Ubuntu`. Ubuntu rejects usernames with capitals; `tarif_420` worked.
4. **Ran `wsl -l -v` inside Ubuntu:** "command not found", because `wsl` is a Windows command. Lesson: know which shell you are in.
5. **`docker` not recognised:** Docker was simply not installed yet. Installed with `winget install -e --id Docker.DockerDesktop`.
6. **Ollama model went to C: despite `OLLAMA_MODELS`:** the Ollama process had started before the variable was set and never saw it. Fixed by moving the files with `robocopy ... /E /MOVE`, then killing all Ollama processes (`Get-Process *ollama* | Stop-Process -Force`; quitting from the tray had not worked) and starting it from the Start menu. General lesson: a program reads settings when it starts.
7. **`.env` lost its defaults and had quoted values:** pasting keys replaced the file contents. Defaults restored and quotes stripped.
8. **`curl` in PowerShell prompted a security warning:** it is an alias for `Invoke-WebRequest`. Use `curl.exe`.
9. **First Dockerfile attempt:** `python:3.9`, `pip install -r requirements.txt` with no `requirements.txt`, and code copied before install (defeats layer caching). Fixed as described in section 6.

## 11. Concepts already explained to the learner

Reuse and build on these; do not re-teach from scratch unless asked:
- What `CLAUDE.md` / `AGENTS.md` do; `.gitignore` and `.gitkeep`; `git add` vs `commit`; the git commands in `docs/git-commands.md`.
- Virtual environments, why they are not committed, `pyvenv.cfg`; what `uv` is and why the PRD prefers it.
- What Docker does (image, container, Dockerfile); why Windows needs WSL2 (Linux kernel for Linux containers).
- What `.env` is for; the two tests for what belongs in it (secret, or differs between environments); the habit of adding each new name to `.env.example`; a rough timeline of what gets added on which day.
- Why the three hello-world checks exist and the basics behind each: HTTP requests and responses, status codes, FastAPI vs Uvicorn, `/health`; embeddings, vectors, cosine similarity (with 2-number worked examples); tool calling (the model only requests, code decides).
- `uvicorn main:app --port 8000` piece by piece; why `python main.py` would not serve anything.
- Ports in detail: address vs port, listening, one listener per port, visitor's random port, `127.0.0.1` vs `0.0.0.0`, Docker port mapping `-p 8000:8000`, `Get-NetTCPConnection -LocalPort 8000 -State Listen`.
- Dockerfile instructions: `FROM`, `WORKDIR`, `COPY`, `RUN` (build time) vs `CMD` (start time), `EXPOSE` (documentation only), build context, layer caching order.
- How to check a service is running (ask its port or `/health`); transferable habits for industry work.

## 12. Exact next step

**Finish check 1, Part B: run the FastAPI app in Docker.** The learner was given these steps and has not reported back:

1. Start **Docker Desktop** from the Start menu; wait for "Engine running".
2. In the VS Code terminal:
   ```powershell
   cd G:\support-copilot\hello\health_app
   docker build -t health-app .
   docker run --rm -p 8000:8000 health-app
   ```
   Expected: `Uvicorn running on http://0.0.0.0:8000`.
3. Open http://localhost:8000/health in the browser; expect `{"status":"ok"}`. Stop with `Ctrl+C`.

The Dockerfile has not been test-built (the engine was off). If the build fails, follow rule 4: ask for the learner's hypothesis, then hint in levels.

## 13. After that, to close Day 0

1. **Langfuse test trace** (Gate G0). Check the installed `langfuse` package version and its current docs before writing anything; its Python SDK API changes between major versions. Variable names are in `.env` as Langfuse printed them.
2. **Confirm the Neon `vector` extension:** in Neon's SQL editor, `SELECT extversion FROM pg_extension WHERE extname = 'vector';`.
3. **Journal:** help the learner fill `docs/journal/day-00.md` in their own words: what they learned, the problems in section 10, the numbers in section 8.
4. **Debug log:** move the section 10 items the learner understands into `docs/debug-log.md`, in their words.
5. **Commit and push** (the learner runs it): `hello/`, `AGENTS.md`, `docs/handoff.md`, `CLAUDE.md`. Remind them to run `git status` first and check no `.env` is listed.
6. **Gate G0 review** with the learner, then start **Day 1** (PRD Section 11.4): Compose file with Postgres + pgvector, schema, hand-written embedding adapter, raw-SQL nearest-neighbour search.

## 14. Open questions for the learner

- Remove rules 3 and 5 (prediction and quiz questions) from the contract, given they asked to stop the questions?
- Move the PRD files into `docs/` to match the contract, or change the contract's wording?
- Re-baseline the PRD dates now that Day 0 ran long.

## 15. Notes for Day 1 and later

- **Disabling qwen3 thinking:** `"think": false` did not fully suppress reasoning in Ollama 0.40.3 (section 8). Check Ollama's current docs before relying on it in the model adapter, and consider stripping text up to `</think>` as a fallback.
- **Embedding dimension is 384:** the `chunks.embedding` column is `vector(384)`.
- **Postgres in Docker on 8 GB RAM:** stop the model (`ollama stop qwen3:4b`) while working on the database, and keep Docker under the 3 GB WSL cap.
- **Versions to pin** when `pyproject.toml` is created: fastembed 0.9.0, fastapi 0.143.3, uvicorn 0.54.0, Python 3.12.
