# CaseFlow support agent: Day 13 deployed MCP integration

The current HTTP workflow and scripts/agent_workflow.py use MCPTools for all graph
reads. It maps search_kb/get_order to the MCP read server using the authenticated
worker bearer, with strict discovery/schema checks and no direct-read fallback.
Human approval and mock refund execution remain outside MCP. The operator's
approval credential is never passed to the read tools or model.

Local Docker agent: http://127.0.0.1:8002; MCP: http://127.0.0.1:8003/mcp.
Inside Docker the agent uses http://mcp-server:8000/mcp. To use the durable CLI,
keep the MCP server running; --mcp-url selects a trusted endpoint. Previous
--knowledge-url/--backend-url flags are removed from that CLI. Historical
scripts/run_agent.py remains the direct-tool baseline, not the current HTTP path.

370 tests passed; live MCP 22/25 (88%); local Docker approval/idempotency smoke
passed. See [local commands and deployment proposal](../../docs/deploy-mcp.md)
and [G3 evidence](../../docs/gates/G3-verification.md). Release bb7491d is deployed;
public MCP-backed approval/resume/idempotency smoke passed with fixture cleanup.

---

Day10 history: authenticated HTTP workflow and opt-in guarded backend execution
were deployed on EC2 in release47906e1 before the current MCP release.
See [current service/deployment guide](../../docs/deploy-agent.md). Earlier sections below are
historical modes; default backend execution remains disabled unless explicitly enabled.

# Historical Day9 local workflow

Day 9 adds durable local approval/rejection, SQLite restart/resume and a guarded
mock refund ledger. Start with the [approval guide](../../docs/approval-flow.md).
The user-approved fictional $75 request completed with exactly one verified receipt.
The HTTP refund route remains disabled. The default loop/Day 8 graph below remain
read-only. The following sections document those earlier baseline modes.

# Support agent — Day 6 bounded loop

The default engine remains the plain loop baseline. Day 8 adds --engine graph. The model
requests reads; Python validates and dispatches them; results return as tool messages.
The only tools are `search_kb(query, top_k)` and `get_order(order_id)`.

## Try it

Prerequisites: [local mock backend](../mock-backend/README.md) running on port 8004,
its agent tokens provisioned in local Postgres, and existing policy-read tokens
in the ignored `.env`. These are already configured in the current session.
The hosted demo Knowledge API must be running at its current IP-encoded hostname;
verify/update that URL after any EC2 stop/start address change.

In another local PowerShell terminal at `G:\caseflow`:

```powershell
.venv\Scripts\python.exe scripts/run_agent.py --provider hosted --knowledge-url https://16-178-30-70.sslip.io --ticket "What is the status of order NW-1042?" --output evals/results/day-06-demo.json
```

Expected successful result: `status: reply`, selected order id NW-1042, status
`shipped`, fictional tracking information, and `refund_executed: false`. A live model
may fail and escalate; inspect the saved reason rather than assuming success.
The hosted configuration uses the existing Groq key with GPT-OSS-20B. It consumes
the free account's inference quota; do not repeatedly rerun without a reason.

For a policy question, the model selects retrieved chunk ids and code returns
their exact text as a draft with citation metadata. For an order question, code
formats selected factual fields from the actual read result. There is no arbitrary
free-form model prose in the returned customer draft. These are evidence-selection
baselines, not a polished conversational assistant or proof of semantic completeness.

## Bounds and security

- Default maximum: 6 model steps, 6 tool calls, 120-second run budget; CLI can
  reduce these. Individual model requests are limited to at most 60 seconds.
- Deadline checks happen before/after calls; this is not an OS-level preemptive
  timer. HTTP timeout behavior is the client's bounded network-phase behavior.
- Native tool schemas forbid extra fields. No model tool takes a tenant, URL,
  credential, approval flag or refund amount. Tool batches are validated before reads.
- A local agent principal needs `agent:run`; each tool also requires its read scope.
  The trusted CLI binds service URLs and credentials outside model control.
- Missing/foreign orders both fail closed. Infrastructure failures do not count
  as successful escalations in the scenario judge. No remote HTTP credential
  destination is allowed without HTTPS, except loopback during local development.
- Unknown tools, malformed arguments/plans, invented chunk ids, provider errors,
  limits and missing evidence escalate without a fabricated reply.
- Every refund proposal escalates to a human. It does not create an approval record
  or execute a refund. The backend independently disables its write endpoint.

Future work: Day 7 policy/25 scenarios; Day 8 graph; Day 9 durable approvals and
traces; Day 10 broader evaluations/security/deployment. Do not claim those features
are complete or expose this operator loop as a public agent endpoint yet.

## Evaluate

```powershell
.venv\Scripts\python.exe scripts/run_agent.py --provider hosted --evaluate --count 5 --knowledge-url https://16-178-30-70.sslip.io --output evals/results/day-06-hosted.json
.venv\Scripts\python.exe scripts/run_agent.py --provider local --evaluate --count 5 --knowledge-url https://16-178-30-70.sslip.io --output evals/results/day-06-local.json
```

Local configuration uses existing Ollama `qwen3:4b`, not a new model download.
It is memory-intensive on this laptop. Run one heavy model at a time; stop it
after testing with `ollama stop qwen3:4b`. Neither command changes a database
order or sends a customer message. Output contains fictional source facts, not
credentials. The first five scenarios are identical between providers.

See [scenario methodology](../../evals/agent/README.md),
[loop/graph comparison](../../docs/loop-vs-graph.md) and the Day 6 journal.

## Day 7 policy and scenarios

The full dataset now contains 25 cases; the original ten remain versioned in
`evals/agent/scenarios-day06.jsonl`. Pure eligibility rules are implemented in
`policy.py`, with cap/ownership/status/scope checks and deny-wins tests. Eligible
refunds still require human approval; every decision disables execution. The
read-only loop is unchanged and does not yet integrate this policy. Day 8 connects
it to the graph; Day 9 implements durable human approval. No approval workflow
or full-dataset model success rate is claimed.

To check policy behavior without a model, in PowerShell at G:\caseflow:

```powershell
.venv\Scripts\pytest.exe -q tests/test_policy.py tests/test_policy_scenarios.py
```

## Day 8 graph

Use `--engine graph` with the same trusted local runner and read-service setup.
See [state, nodes, diagram and exact command](../../docs/agent-graph.md) and
[25-case comparison](../../evals/results/day-08-summary.md). The graph uses the
code policy. Eligible synthetic contexts reach a non-durable required-approval
marker; the real demo CLI supplies no customer identity and existing credentials
lack refund scope. There is no approval-to-execute path. Durable approval and
restart/resume remain Day 9 work. Earlier Day 6/7 sections above are historical.
