# Handoff: project state as of 19 October 2026

## Explicit deployment approval and release preparation: 27 October 2026

User explicitly approved exposing authenticated MCP on existing EC2 and adding
the two existing read-only MCP token hashes to Neon. This supersedes older
approval-blocked notes below. Do NOT ask the same permission again. No actual
deployment or production provisioning has run yet; USER release commit/push and
successful fresh CI remain the prerequisite. Do not commit/push for the user.

- Approved cloud Compose prepared: support-copilot-agent project retained;
  caseflow-mcp image, loopback8003,512MiB cap, non-root image, dropped capabilities,
  no-new-privileges, explicit internal/public hosts, existing embeddings volume.
  Agent fixed MCP_SERVER_URL internal; existing Knowledge URL retained for rollback.
- New deploy_mcp_ec2.sh requires full40char exact clean HEAD and successful latest
  main/push CI before secrets/updates, plus existing proxy/volume and >=600MiB
  available memory. Reads only existing DATABASE_URL/LLM_API_KEY SSM paths in
  memory. Builds three images; validates Caddy candidate; waits for services;
  adds /mcp and /mcp/* while preserving /agent/* and Knowledge routes.
- Saves prior image refs/proxy contents in .cache/day13-rollback-RELEASE_PREFIX.
  Automatic rollback on update failure; explicit --rollback supported. Keeps
  proxy bind inode/certs/data; old deploy_agent_ec2.sh delegates to new helper.
- New provision_mcp_cloud.py adds only existing NORTHWIND/CONTOSO_MCP_API_TOKEN
  hashes to configured Neon with kb:read/orders:read/tickets:read. Atomic,
  idempotent, rejects mismatched/revoked/expired rows. Raw values never printed
  or copied to cloud files. Run only AFTER exact release CI passes.
- check_mcp_http.py accepts --url and compares foreign/missing order errors for
  both tenants. Local final check passed, evidence day-13-local-mcp-smoke.json.
- 370 tests passed in29.22s. Five new credential tests in LOCAL test DB. Linux
  deployment harness passed with mocked commands/no network, including automatic
  rollback before/after proxy edits, explicit rollback and failed-CI refusal.
  Real Compose/Caddy config checks passed with dummy values; no real startup.
  CI now runs harness+config checks as well as tests and four image builds.
- Initial harness run needed exec-enabled isolated /tmp for executable test stubs;
  fixed only test-container setup. Approval-review usage-limit failure did not
  execute; user said carry on, retry completed. No security review bypass.
- NEXT: user commits/pushes full Day13 release; read exactSHA and CI. Then run
  provision_mcp_cloud.py; SSH verifiedcurrentIP, update existing ~/support-copilot,
  deploy exactSHA using deploy_mcp_ec2.sh. Run public MCP SDK+Inspector, synthetic
  agent --require-mcp --database neon, existing KB smoke, and capture EC2 stats.
  docs/deploy-mcp.md has sequence/rollback. G3 still pending public evidence.

## Public deployment approval follow-up on 27 October 2026

User replied "do what is necessary" to the deployment proposal. Read-only SSH to
16.178.30.70 verified current checkout47906e1, original Day10 agent/backend images,
Knowledge531d7c4, Caddy2.11.7,999MiB available RAM and existing embeddings volume.
The attempted concrete patch was rejected AGAIN by automatic approval review:
it requires explicit authorization for public MCP topology AND provisioning two
existing read-only MCP token hashes in production Neon. No cloud patch or token
mutation performed; compose.agent-aws.yaml unchanged and provision_mcp_cloud.py
not created. Do not bypass or keep retrying without explicit approval/evidence.
docs/deploy-mcp.md now lists the two exact actions to approve. Local Day13 remains
verified as below; no new commit/push by agent. Await that approval, then prepare
the patch, user release commit/push, CI and deployment/public checks.

## Day 13 local verified on 27 October 2026; public approval pending

- Current agent API and durable CLI use MCPTools, no direct-read fallback. Fixed
  search_kb/get_order mapping, exact registry/schema checks, read annotations,
  bound worker token/URL, 128,000-byte response limit and max 20s whole read budget.
  SDK 1.30.0 reused; no dependencies changed. Historical direct-loop script retained.
  Refunds remain on the guarded internal backend and distinct human approval ledger.
- Live hosted MCP evaluation 22/25 (88%); saved direct 21/25 (84%). Same immutable
  order/corpus fixtures, exact random local namespaces copied then cleaned. Direct
  control replayed identical model choices and verified model input digests;
  25/25 final results matched except elapsed time/diagnostics. Replay is NOT
  independent inference. Seven recovered rate-limit retries. Fails s001/s002/s012.
  Quality eval uses a non-durable approval marker and executes no refunds.
- 365 tests passed in 29.80s, including all Postgres integration. Eight injection
  surfaces through direct+MCP adapters pass 16/16; not a live-model immunity claim.
  Dedicated G: temp path resolved Windows default pytest-temp ACL failures.
- Added non-root services/mcp-server/Dockerfile and CI build. Built local images
  caseflow-mcp/agent/backend:day13. Local Compose project support-copilot preserved;
  MCP loopback8003 -> container8000, agent8002, internal backend, existing KB/db.
  Host Uvicorn PID8360 stopped before Docker took port8003; no host MCP listener.
- Local Docker smoke passed actual MCP order lookup, durable pause, scoped/foreign/
  forged resume rejection, synthetic operator decision, resume and exactly one
  mock receipt after retry. Temporary smoke tenant/checkpoints removed. Existing
  demo refund history preserved. No real or existing customer approval performed.
- Official Inspector2.12.0 with isolated Node24.22.1 legacy mode listed/called all
  three tools over HTTP. New JS wrapper uses installed runCli with auth header in
  memory, never OS argv/config files. No UI screenshot claim. Both checker and
  smoke accept explicit public options for later authorized release verification.
- Evidence day-13-agent-mcp.json, day-13-injections.json,
  day-13-local-agent-smoke.json, day-13-local-inspector.json. Architecture.md,
  decision007, journal day13 and docs/gates/G3-verification.md updated.
- IMPORTANT: automatic approval review rejected the AWS Compose/proxy patch to
  add public MCP exposure. Patch was NOT applied. No workaround or cloud change.
  compose.agent-aws.yaml is unchanged. deploy_agent_ec2.sh has a fail-safe preflight
  refusing that old topology. Concrete target/routing/limits/rollback proposal in
  docs/deploy-mcp.md: existing Sydney i-073581e82c41622ea, current documented host
  16-178-30-70.sslip.io; public HTTPS /mcp, private loopback8003, existing IAM/SSM
  and volumes. Verify current IP before deployment. No new paid resource planned.
- NEXT: request explicit user approval for that public target/scope. After it,
  prepare/review cloud patch, USER commits/pushes, verify fresh CI, deploy exact
  reviewed commit, then public Inspector/MCP/agent/existing KB smoke. Do NOT claim
  Day13 or G3 complete yet. Learner explanation remains deferred, never passed.

## Folder move verified on 27 October 2026

Current workspace is G:\caseflow; G:\support-copilot no longer exists. Recreated
.venv, Python executable, import package and PROJECT_ROOT resolve to the new
workspace; CLI help runs. Git remote is Tarif205/caseflow.git. Rename commit
35ce4929cedc656c47f0da703f68ba6fc9de7a97 was independently verified on GitHub main
before moving. Current docs now use the new Windows path. No cloud deployment
or database/volume rename. Older pending-move notes below are superseded.


## CaseFlow rename on 27 October 2026

User chose CaseFlow before Day 13. Source package/distribution/CLI now caseflow;
imports, Docker entrypoints, API titles and current docs updated. PRD Markdown is
CaseFlow_PRD.md. AGENTS.md and CLAUDE.md updated together without changing the
learning contract. CASEFLOW_PROJECT_ROOT preferred, COPILOT_PROJECT_ROOT fallback.
Historical notes/evidence below use the old names accurately; read current service
READMEs for runnable commands. No cloud deployment performed for this rename.

Current workspace remains G:\support-copilot. USER renamed the GitHub repository;
agent updated origin to https://github.com/Tarif205/caseflow.git and verified
ls-remote HEAD 8e0a543c4860261b3fc98e09c27d456f400c2aa0. No commit/push by agent.
Editor closure/folder move/virtualenv recreation remain USER steps documented in
docs/rename-caseflow.md. Do not claim the folder move completed. Preserve
existing Compose project/volume/DB/SSM/IAM/proxy identifiers, key and EC2 checkout;
mapping is in the rename guide. User commits and pushes. Day 13 remains next.

Rename verification: 343 tests passed in 29.90s; lint/format clean. All three
caseflow-*:rename Docker images built; packaged schema/root/CLI verified in
network-disabled containers. New stdio/HTTP evidence caseflow-rename-*.json asserts
caseflow-readonly metadata for both tenants. Old evidence unchanged. Local MCP
listener is now caseflow.mcp_http:app port 8003, ignored .cache/caseflow-rename-mcp.*
logs. Docker Desktop initially closed; started it and existing DB, reran suite
successfully. No old data volumes or deployed service containers replaced.

## Latest update on 26 October 2026

### Day 12 MCP HTTP verified: next implementation is Day 13

- Added mcp_http.py: official SDK 1.30.0 Streamable HTTP, stateless JSON responses,
  loopback http://127.0.0.1:8003/mcp. Fresh bearer authentication per request,
  operation scopes and rechecked read authorization. Identity uses the SDK message's
  exact request context, never a shared caller field or model arguments.
- No session IDs issued; all incoming session headers rejected. GET/DELETE 405
  after auth. No token query parameters. Explicit Host/Origin allowlists, duplicate
  and malformed auth rejection, 16 KiB body bound. Request logs contain generated
  ID/method/status/duration only. Process environment MCP_ALLOWED_HOSTS and
  MCP_ALLOWED_ORIGINS configure nondefault hosts; these are not loaded from .env.
- Added resource template kb://article/{id}: kb:read, tenant-filtered documents and
  original overlapping chunks, bounded to 64 chunks/4000 chars each/64 KiB JSON.
  No file or external URL reads, global document enumeration or foreign existence
  detail. Added draft_support_reply(ticket, article_id), strict bounded args,
  instructions plus untrusted JSON evidence; no model call/action. Stdio retained.
- **343 tests passed in 27.23s**, Ruff lint/format clean. Seventeen new cases cover
  concurrency, expiry/revocation/scopes/forged sessions, resource/prompt isolation,
  hostile headers and input bounds. Real concurrent SDK HTTP clients for both
  tenants called all tools, read different article content at the same URI and
  prepared the prompt; no session IDs, negotiated 2025-11-25. Evidence:
  evals/results/day-12-http.json, checked_at 2026-10-26T17:31:29.749418+00:00.
- Current local background Uvicorn serves port 8003; logs ignored in
  .cache/day12-mcp-final.stdout.log and .stderr.log. Do not start a second listener.
  No package/schema/token/cloud changes or model calls. Existing EC2 services
  remain untouched. This is project bearer authorization, not full OAuth
  discovery/issuance/audience binding/third-party consent or latest-spec support.
- Docs: services/mcp-server/README.md, docs/mcp-threats.md, decision 006 and journal
  day-12. Learning checks deferred, never passed. Next concrete step: USER
  commit/push Day 12. Day 13: agent as MCP client, deployment and integration proof.

### Day 11 stdio MCP verified: current next implementation is Day 12

- Added mcp_server.py using locked official SDK 1.30.0 low-level Server. Three
  tools only: search_knowledge_base, get_order_status, list_open_tickets.
  Strict Pydantic input/output schemas; extra identity/URL/approval fields rejected;
  projected outputs exclude tenant/token/internal metadata. Query/count bounds.
- Added connect(read_only=True) for MCP; default other-service behavior unchanged.
  Scope/active-token/tenant checks reused per read, model never supplies identity.
  New local .env credentials NORTHWIND_MCP_API_TOKEN / CONTOSO_MCP_API_TOKEN have
  only kb:read, orders:read, tickets:read. Hashes in LOCAL DB only; no cloud change.
  MCP_TOKEN_ENV is a launcher setting selecting credential name, not tool input.
- Real SDK stdio checks initialized/listed/called all tools for both tenants and
  rejected foreign read, injected tenant and write tool. Negotiated 2025-11-25;
  CURRENT spec checked is 2026-07-28, so do not claim latest-spec support.
- Official Inspector 2.12.0 CLI, explicit legacy era, listed/called all tools.
  Uses isolated Node 24.22.1 via npm cache G:/npm-cache; system Node still 22.16.0.
  Cache already populated; scripts/check_mcp_inspector.py runs offline. No Python
  dependencies changed, no global runtime upgrade or UI/screenshot claim.
- **326 tests passed in 27.02s**, lint/format clean. 18 new tests include schema
  rejection before IO, exact projections, scoped/foreign/missing reads, revocation
  and actual SQL read-only enforcement. Evidence day-11-stdio.json and
  day-11-inspector.json. Inspector/SDK smoke processes finished; no new listener.
- Docs: services/mcp-server/README.md tool table/setup, decision 005, journal day-11.
  No chat model calls, refunds, MCP HTTP/resource/prompt/deployment for Day 11.
  Existing EC2 stacks/roles preserved. Learning checks deferred, never passed.
- Next concrete step: USER commit/push Day 11. Next PRD implementation Day 12:
  Streamable HTTP per-request auth/header/isolation tests, article resource,
  draft prompt and threat table. Day 13 agent-as-MCP-client/deployment remains later.


### Day 10 deployed and public smoke verified: supersedes release-pending notes

- User pushed 47906e1b13eaf4f7318ad38e9777082b04ab5030. GitHub Actions run
  40340314622 completed SUCCESS, independently read via public API from EC2
  after local public API rate limit; connector returned no push runs. Evidence
  evals/results/day-10-release-ci.json. No assistant commit/push.
- Additive Neon schema/Postgres checkpoints/mock fixtures initialized; existing
  local WORKER/APPROVER role hashes provisioned in Neon. No raw secret copied or
  printed, no existing credentials changed. Initial deploy attempt did not execute
  because automatic review hit a usage limit; user said carry on, retry passed.
- Exact reviewed commit deployed on existing Ubuntu EC2. Images:
  support-copilot-agent:47906e1b13ea and support-copilot-backend:47906e1b13ea.
  Existing Knowledge API image/container remains 531d7c4, not replaced.
- Public base https://16-178-30-70.sslip.io/agent; Caddy 2.11.7 persists /agent/*
  routing to loopback 8002 and other routes to existing loopback 8001. Backend
  has no published port. Old proxy retained stopped as
  support-copilot-proxy-before-agent for rollback; cert volumes reused.
- **Public HTTPS agent smoke PASSED**: health/readiness/missing auth, durable
  approval pause, tenant/scope/forged resume blocked, distinct synthetic operator
  decision, resume and exactly one mock receipt after retry. Its exact temporary
  Neon tenant and checkpoints removed. No seeded demo/customer request approved.
  Evidence day-10-public-agent-smoke.json, checked_at 2026-10-26T16:24:59+00:00.
- Original Knowledge API's full public smoke PASSED after proxy change, including
  both tenant searches, order refusal and real cited warranty answer. Evidence
  day-10-existing-knowledge-smoke.json, checked_at 2026-10-26T16:27:51+00:00.
- EC2 memory snapshot MiB: Knowledge 236.9, agent 91.89, backend 59.64, proxy 10.42.
  Not peak/load evidence. Build startup curls retried connection resets and recovered.
  Evidence day-10-ec2-deployment.json. No new EC2 resource/IAM expansion/paid plan.
- **G2 technical release checks verified.** Hosted 84%, local 88%, 308 tests,
  eight enforcement cases and Postgres restart evidence remain as below. Manual
  trace screenshot and learner explain-back remain deferred, never passed.
  Deployed tracing remains disabled until credentials are supplied securely;
  only local Day 9 trace export was verified. Do not claim cloud trace export.
- **Next:** user saves deployment evidence/docs with normal commit/push; next PRD
  implementation is Day 11, read-only MCP server. Preserve deployed stacks and
  role boundaries. Current IP can change on EC2 stop/start; verify it first.


### Day 10 local verification complete: user release commit is next

- Added strict graph JSON schemas (Groq max_tokens 1200, low reasoning; Ollama
  schema format), safe provider status/code/time/token diagnostics and one bounded
  Retry-After retry. Initial hosted 14/25 had eight CONFIRMED HTTP 429 failures.
  Paced hosted run 21/25 (84%), local 22/25 (88%). All three full reports retained.
- New evaluation runner scripts/evaluate_agent.py uses immutable order fixtures,
  real KB reads and explicit trusted fixture identity/scopes. Approval is a
  non-durable required marker in quality eval; actual durable approval tested
  separately. Do not claim held-out, intrinsic model or semantic completeness.
  Dataset version scenarios-day07.jsonl preserves old Day 7/8 hashes. s023 now
  explicitly accepts secure early foreign-order 404. New hash begins 6c4aa884.
- Eight deterministic hostile-model/data injection cases pass. PostgresSaver 3.2.0
  checkpoint backend passes separate-process restart/no-model-replay/one-receipt
  test. SQLite CLI remains compatible. qwen3 unloaded after the 25-case run.
- Added agent_api.py: bearer tenant/scopes, stored-ticket intake, ownership-bound
  status/resume, separate operator decisions. Resume takes no approval body.
  Same-run Postgres advisory locks serialize resumes. API forwards incoming worker
  token to read services on the shared authority; no extra server tenant keys.
- Mock backend POST /refunds now opt-in (MOCK_REFUNDS_ENABLED=true). Accepts only
  run_id; reuses authoritative ledger with current worker/operator authority,
  policy, snapshot, row locks and idempotency. Default/manual old backend stays
  disabled. Docker API executes through this actual internal HTTP route.
- **308 tests passed in 31.47s**, lint/format clean. Both new non-root service
  Docker images build, no .env/Git history. CI builds all three service images.
  Local Docker HTTP smoke passed: durable pause, missing/foreign/scope/forged
  resume rejection, simulated operator approval, actual backend execution and
  exactly one receipt after retry. Synthetic namespace/checkpoints removed.
- Local support-agent at 127.0.0.1:8002, internal mock backend in Compose. Both
  running; existing dev/cloud stacks preserved. Memory snapshot agent 97.98MiB,
  backend 61.93MiB, not a peak/EC2 measurement. Evidence day-10-*.json.
- Prepared compose.agent.yaml, compose.agent-aws.yaml, cloud schema/hash helper,
  reviewed-commit EC2 deploy script with persistent Caddy /agent routing and rollback.
  Read-only SSH works; EC2 checkout STILL 531d7c4. NO Day 10 cloud schema, role
  hash or deployment change yet. No plan upgrade/new paid resources/dependencies.
- **Next:** user commits/pushes Day 10 and verifies fresh CI, then assistant can
  run scripts/provision_agent_cloud.py, deploy reviewed commit over verified SSH
  using scripts/deploy_agent_ec2.sh and run scripts/smoke_agent.py against public
  /agent with --database neon (isolated synthetic smoke). No approval of an
  existing demo/customer request. Preserve the existing Knowledge API container.
  See docs/deploy-agent.md for sequence and rollback. Do not ask for secret values.
- G2 remains open pending fresh CI/public deployment smoke. Learning explanation
  checks remain deferred; do not start Day 11 until technical G2 is verified.


### Day 9 functionality and human-approved demo verified

- Added durable_agent.py with SQLite checkpoints, real interrupt/resume and
  authenticated stored-ticket/customer binding. Postgres agent_runs,
  refund_approvals and refunds are authoritative; resume data never grants approval.
- Local CLI scripts/agent_workflow.py supports start/pending/approve/reject/resume.
  Distinct worker/operator identities, strict scopes, expiry/revocation checks,
  ownership, cap, immutable proposal/order snapshot and transactional idempotency.
  One refund per order; a partial also closes the fictional order. HTTP POST
  /refunds remains 501; local execution calls the guarded repository. Day 10 must
  wire that same boundary into the deployed internal backend.
- New local .env settings NORTHWIND_WORKER_API_TOKEN (read/agent/propose/execute)
  and NORTHWIND_APPROVER_API_TOKEN (refund:approve). Values not printed/copied;
  hashes only in local DB. Existing read tokens unchanged; no cloud migration.
- **291 tests passed in 16.87s**, including real Postgres, cross-process pause/
  simulated approval/resume with no model replay and one receipt after repeated
  resume. Forged resume/rejection/missing scope/expiry/revocation/order or amount
  changes fail closed. Committed receipt not erased by a later deadline check.
- Langfuse metadata-only run/node spans; safe failed intake trace delivery and
  reason verified through read API. No prompts/customer data/keys/raw errors.
  Evidence day-09-failed-trace.json. Browser tool failed local kernel asset setup;
  UI screenshot NOT captured, remains manual. API evidence is not a UI screenshot.
- **LIVE DEMO COMPLETED BY USER:** run 152af441-f371-43fd-9f01-b8626f8c9585,
  ticket NW-T002/order NW-1044, $75 (7500 USD cents). User explicitly ran approve,
  then resume --trace. Returned refunded/approved_mock_refund with durable approval.
  Read-only ledger verification confirms approved decision, order refunded and
  exactly ONE receipt. Evidence: evals/results/day-09-live-approved.json. Resume
  trace URL is user-reported; failed-trace delivery was independently API-verified.
  No assistant approval or execution. Next: user commit/push, then Day 10.
- Files: .cache/agent-checkpoints.sqlite (ignored), docs/approval-flow.md,
  docs/approval-graph.mmd, docs/journal/day-09.md and Day 9 JSON evidence.
  Checkpoint includes fictional ticket/evidence, never service credentials.
- Next PRD step: Day 10 diagnostics/eval/injection tests, Postgres
  checkpointer and service deployment/G2. G2 is still open (last hosted 14/25).
  Default Day 8 graph remains read-only. User commits/pushes; learning deferred.

### Day 8 implementation complete: current next step

- Added agent_graph.py using installed LangGraph 1.2.16, verified official API.
  Typed state and nodes intake/retrieve/lookup/plan_action/policy_check/approval/
  draft_reply/escalate. Execute is unreachable and independently disabled.
- Structured JSON models for intake/planning; no identity/scope/approval model
  arguments. Trusted identity/dependencies outside state. Reply still renders
  only original chunks/whitelisted facts. Code refund policy integrated.
- Eligible synthetic context reaches a terminal, NON-DURABLE approval marker.
  No checkpoint/interrupt/resume, approval record, tracing, execution or deployed
  agent yet. Real CLI supplies no end-customer identity and existing tokens lack
  refunds:propose; no permissions were widened to improve model scores.
- 266 tests passed (7.42s) with Postgres integration. All graph paths, safe errors,
  evidence/identity injection, failed-read counting and time/tool/node budgets covered.
- Real 25-case hosted comparison: graph 14/25, hand loop 10/25; first five 5/5
  versus 4/5. Graph had nine model_unavailable failures, one correct policy denial
  under missing identity/scope and one correct foreign-order 404 failing a strict
  downstream policy label. No per-case upstream status retained; cause not proven.
  Separate small/normal token probes returned 400/200 and do not diagnose those cases.
- Results day-08-graph-hosted.json, day-08-loop-hosted.json and day-08-summary.md.
  Same scenario hash, but sequential runs, changed model protocols and step units;
  do not claim a controlled framework benchmark. All 50 results show no refund.
- Generated docs/agent-graph.mmd, state/path guide, updated loop-vs-graph table,
  journal. No dependency/schema/credential/cloud changes. Local model not loaded.
- **Next: Day 9**, persistence, durable human approvals and tracing. G2 remains
  open; 56% is below Day 10's 60% quality gate. Reconcile the foreign-order fixture
  expectation and improve safe per-call provider diagnostics before that gate.
  User commits/pushes; fresh CI not yet confirmed. Learning checks deferred.

### Day 7 complete: current next step (supersedes Day 6 below)

- Added pure policy.py: strict immutable inputs, no IO/model/writes. Refund rules:
  positive integer cents, fixed $80 USD cap, order-total bound, delivered status,
  tenant/customer/order match, explicit agent:run and refunds:propose scopes,
  deny-wins precedence. All decisions disable execution; eligible means needs_approval.
- Customer identity must come from trusted intake, never ticket prose. Existing
  tokens gained no scope. Policy integrates in Day 8; loop/backend remain read-only.
- Expanded scenarios to 25, ten deterministic refund cases (two eligible/eight
  denied). Preserved original ten byte-for-byte as scenarios-day06.jsonl; hashes
  match both model reports. Runner supports --scenarios and --count up to 25.
  Generic escalation cannot count as policy/approval success. No new live model run.
- Full local suite **245 passed in 6.92s**, including Postgres integration tests.
  Each denial covered; finite exhaustive property check covers 1,260 combinations.
  See docs/decisions/004-refund-policy.md and docs/journal/day-07.md.
- No cloud/schema/dependency/credential changes for Day 7. Day 6 real model results
  unchanged. Pending work awaits user commit/push and fresh CI. No assistant commit.
- **Next: Day 8**, LangGraph rebuild with code policy and non-executing approval
  placeholder. Durable approval is Day 9. Learning checks remain deferred.

### Day 6 complete — current next step

- Built a local tenant-bound mock backend: composite Postgres customers/orders/
  tickets, 3/5/4 synthetic fixtures, idempotent insert-only seed, authenticated
  orders/tickets reads, request-id logs and generic errors. POST /refunds is
  always disabled (501); no approval/ledger/execution is claimed.
- Added plain bounded native-tool loop, separate Groq/Ollama tool adapters,
  strict search_kb/get_order argument schemas, actor scopes and evidence-only
  final rendering. Defaults: six steps/six tool calls/120s boundary budget;
  each model call max 60s. No tool can accept tenant/URL/credential/approval fields.
- New local agent tokens were generated into ignored .env as
  NORTHWIND_AGENT_API_TOKEN and CONTOSO_AGENT_API_TOKEN; scopes kb:read,
  orders:read, tickets:read, agent:run. Only hashes stored in LOCAL Postgres;
  no new tokens/schema were applied to Neon. Existing knowledge credentials unchanged.
- Backend is running on laptop loopback 8004 (started hidden for verification).
  /health 200 verified. See services/mock-backend/README.md for setup/start commands.
- First 10 synthetic scenarios written before real runs. Same first five evaluated
  with Groq GPT-OSS-20B and local qwen3:4b, using real mock HTTP reads and deployed
  policy retrieval. Hosted **4/5**, local **0/5**. Hosted s001 failed invalid final
  output after a successful search; local had one model_unavailable and four
  invalid_model_output failures, all before reads. Do not invent more specific
  provider error causes: raw error/reasoning bodies were not retained.
- Artifacts: evals/results/day-06-hosted.json, day-06-local.json and day-06-summary.md.
  Hosted minimum 3/5 met. Synthetic/in-sample evidence/field checks, not a held-out
  semantic benchmark or the full 25-case evaluation. No refund executed.
- **196 tests passed**, lint/format clean. New tests include loop/tool/time bounds,
  unknown tools/extra tenant args, invented evidence, native wire schemas, backend
  isolation/scopes/expiry/revocation, seed preservation and disabled refunds.
- Local model was stopped after five attempts; ollama ps shows none loaded.
  The existing EC2 API remains on 531d7c4, unchanged. Day 6 agent/backend are local,
  not deployed. LangGraph, deterministic refund policy, durable approval and MCP
  remain pending; loop-vs-graph table marks graph behavior as planned.
- Immediate review: user can run the hosted order demo in services/support-agent/
  README.md; code/docs/evidence await USER commit/push and fresh CI. No assistant
  commit/push. Learning checks deferred. **Next PRD step: Day 7**, complete 25
  scenarios and pure policy (cap, ownership, order eligibility, deny-wins tests).

### Current deployment status — supersedes the stopping point below

User resumed work. Role `support-copilot-ec2-role` was created (screenshot), and
user reported creation of inline policy `support-copilot-read-parameters` allowing
ssm:GetParameter/GetParameters on exactly the two Sydney parameter ARNs. The EC2
Security tab screenshot confirms role attachment. Existing instance was restarted;
current public IPv4 reported by screenshot is **16.178.30.70** (verify after any
future stop/start). Do not use the older 13.210.138.248 address.

- User confirmed checkout `531d7c4` and image
  `sha256:df9d03e1bb9593dcb6dc425ebab74951f455859043de7d1d99429f02c33abbf4`.
- Installed AWS CLI on Ubuntu; reported version 2.38.5. STS output confirms the
  instance role identity, without configured static access keys. Parameter Store
  GetParameters with decryption succeeded for both expected SecureStrings; no
  missing parameters. Only names/types were printed.
- User started `support-copilot-knowledge` with the 531d7c4 image, restart
  unless-stopped, 768 MB memory limit, rotated logs, persistent embedding cache,
  host loopback binding 127.0.0.1:8001 -> container 8000 and Groq GPT-OSS-20B.
  Credentials were loaded via Parameter Store into exported shell variables,
  passed by variable name with sudo --preserve-env, then unset. No .env was copied
  to EC2. Docker retains environment in privileged container metadata; do not
  dump docker inspect configuration or claim secrets are only ever in RAM.
- User output confirms container Up, /health 200 and /ready checks database and
  embedding true. Embedding cache downloaded successfully.
- Full real smoke **passed through encrypted SSH tunnel**, from laptop port
  18001 to EC2 loopback 8001. Evidence file verified locally:
  `evals/results/day-05-ec2-ssh-smoke.json`, checked_at
  2026-10-25T16:39:35.869938+00:00. Includes health/readiness 200, missing token
  401, both tenant searches isolated, order-specific refusal and a real verified
  warranty quote citing warranty.md. No API keys or tokens in artifact.
- Tunnel must run in a LOCAL Windows PowerShell terminal, not Ubuntu. A second
  local terminal runs smoke_knowledge.py with base URL http://127.0.0.1:18001.
  A silent ssh -N process is expected, not a failed connection.
- User saved inbound rules for TCP 80/443 from Anywhere-IPv4, preserving SSH
  restricted to the original /32 IP. Screenshot reviewed before saving. API
  port 8001 and database port 5432 were not opened publicly.
- User started `support-copilot-proxy` from official `caddy:2.11.7`, with host
  networking, 256 MB limit, restart unless-stopped, rotated logs and persistent
  /data and /config volumes. Reverse proxy: 16-178-30-70.sslip.io -> 127.0.0.1:8001.
  Logs supplied by user confirm successful Let's Encrypt certificate issuance;
  the HTTP/2/3 warnings concern plaintext port 80's redirect listener, not failure
  of HTTPS. No access-log capture of request credentials was enabled.
- **Public HTTPS smoke passed**, including actual model output and source quote
  validation: `evals/results/day-05-public-https-smoke.json`, timestamp
  2026-10-25T20:39:18.174217+00:00 (26 October in Asia/Dhaka). All seven checks
  passed for https://16-178-30-70.sslip.io. This verifies the public deployment,
  not just SSH forwarding. TLS verification was enabled; no insecure bypass.
- User measured API memory 348.9 MiB/768 MiB and proxy 11.14 MiB/256 MiB; EC2
  reports 1.9 GiB total, 1.1 GiB available, zero configured swap. This is a snapshot,
  not peak/load-test evidence. Manual API container restart recovered. An immediate
  curl saw connection reset during startup, then container Up and /ready passed.
- Full public smoke passed again after that restart. Evidence:
  `evals/results/day-05-public-after-restart.json`, timestamp
  2026-10-25T20:43:19.750882+00:00. Automatic crash recovery/reboot was not tested;
  unless-stopped is configured, not equivalent to a tested process crash.
- Added reusable actual API refusal evaluator in refusal_evaluation.py plus
  scripts/check_refusals.py. Run against public HTTPS: **10/10 refused, 0 errors**,
  complete=true, 8 no_evidence and 2 record_lookup_required, top_k=5. Evidence:
  `evals/results/day-05-public-refusals.json`, timestamp
  2026-10-25T20:46:28.514185+00:00. All were deterministic pre-model refusals;
  this does not establish model refusal quality, answerable coverage or held-out
  generalization. Corpus/default threshold unchanged.
- Latest validation: 9 new evaluator tests passed, all non-integration tests
  **99 passed, 54 deselected**, lint/format clean. Full-suite rerun was interrupted
  after local DB connection timeouts; read-only docker inspection confirms local
  Docker Desktop engine is stopped. Prior 144-test baseline and deployed 531d7c4
  CI passed; do not claim a fresh full-suite pass for the new evaluator yet.
- User pushed `7c2f4fe` (deployment/evaluator/evidence); local HEAD and origin/main
  match. User reports its GitHub checks green. Docker Desktop is now running.
  Fresh complete local run: **153 passed in 8.46s**, including all integration tests.
- Fresh local Git clone of committed 7c2f4fe, without .env or working-tree files,
  passed Compose build/up/health/readiness and actual authenticated tenant searches.
  Used a separate project, brand-new DB/cache volumes and a port-only isolation
  override (API 18011, no published DB); no cloud credentials or chat-model calls.
  Fresh import matched 15/30 Northwind and 3/6 Contoso. Temporary synthetic tokens
  were not printed. A separate test application with deliberately wrong demo DB
  credentials returned health 200/ready 503 without exposing credentials.
  Evidence: `evals/results/day-05-clean-clone.json`. Temporary containers and
  their volumes were removed; existing local/cloud stacks were preserved.
- G1 technical checks now have evidence; see `docs/gates/G1-verification.md`.
  The original learning explain-back remains deferred, never passed. Latest clean
  checkout evidence/report are local and await the user's normal commit/push.
  **Next implementation step:** Day 6 mock orders/tickets backend and bounded
  support-agent tool loop, preserving refund approval and tenant isolation.
  No agent/MCP work begun. The API can stay on 531d7c4: subsequent changes add
  operator tools/docs rather than serving behavior. No assistant commit/push.

### Stopping point saved on 24 October 2026

Historical pause, now superseded by the resumed deployment status above. The user
had explicitly stopped work until tomorrow and reported EC2 **Stopped**.

- User pushed commit `531d7c4`; their screenshot confirms GitHub CI passed.
- After an initial build accidentally used the old checkout, the user pulled
  `531d7c4`, verified HEAD, and rebuilt. Actual new image id: `df9d03e1bb95`,
  tagged `support-copilot-knowledge:531d7c4`. API has not started on EC2.
- Neon is seeded and API token hashes are provisioned as recorded below.
- In AWS Parameter Store, the user created `/support-copilot/DATABASE_URL`;
  screenshot confirms Standard/SecureString. User reported creation of
  `/support-copilot/LLM_API_KEY` using the same instructed settings. Values were
  not shared. Default AWS-managed key alias/aws/ssm was instructed; actual
  decryption/access has not yet been tested.
- IAM role setup has **not started**. Resume from IAM -> Roles -> Create role ->
  AWS service -> EC2, then establish narrowly scoped access to the two parameters.
- EC2 was stopped at the user's request to conserve credits, not terminated.
  Disk/image remain; storage can consume credits while stopped. On resume,
  start the existing instance in Sydney (ap-southeast-2), wait for status checks,
  and verify its current public IP before reconnecting; the old IP may change.
- Next operational work after IAM: attach role, securely obtain runtime settings,
  start API, configure HTTPS and verify deployed requests. Do not ask for secret
  values in chat or assume instance-role/Parameter Store access already works.
- No Day 5/G1 completion, public API, agent or MCP completion is claimed.
  Learning checks remain deferred. Assistant made no commit/push.

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
