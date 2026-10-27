# CaseFlow three-minute demo

Status: recording guide prepared; no video or rehearsal claimed. Use fictional data
only. The deployed application's previous successful checks are saved under Day 13;
opening an old report is evidence review, not a fresh execution.

## Prepare in PowerShell

Open `G:\caseflow` in VS Code. Start Docker Desktop. The current local application
uses Postgres on 5432, Knowledge 8001, agent 8002 and MCP 8003. Follow the root README if
starting from a fresh checkout. Keep `.env`, keys, authentication headers and account
pages out of the recording. OBS or your existing screen recorder is sufficient;
no paid tool is needed.

For fresh local checks:

```powershell
cd G:\caseflow
docker compose -f compose.yaml -f compose.agent.yaml up -d --wait --wait-timeout 300
uv run --frozen python scripts/smoke_knowledge.py --skip-model --output .cache/demo-knowledge.json
uv run --frozen python scripts/check_mcp_http.py --timeout-seconds 180 --output .cache/demo-mcp.json
```

Both commands need the local scoped token names provisioned in the README. They
print safe results, not credentials. They do not approve a stored request.

For the approval sequence, use the isolated synthetic smoke below. It needs your
configured chat provider key and consumes its quota. It simulates the operator
only for a temporary fixture it creates and removes; it does not approve a stored
demo/customer request. The report summarizes its real HTTP workflow.

```powershell
uv run --frozen python scripts/smoke_agent.py --base-url http://127.0.0.1:8002 --database local --require-mcp --output .cache/demo-agent.json
```

Success includes `durable_approval_pause`,`tenant_scope_and_forged_resume_blocked`,
`exactly_one_mock_refund_after_retry`,`complete: true` and fixture cleanup.
If provider quota blocks the run, show the saved public report and label it recorded
evidence; do not present it as a fresh live run. Do not repeat an old approved run
or approve an existing pending customer/demo request just to obtain a recording.

## Storyboard

| Time | Screen/action | Suggested narration |
|---|---|---|
| 0: 00-0: 25 | README diagram | CaseFlow handles fictional support for two tenants. Evidence reads and refund authority are separate. |
| 0: 25-0: 55 | Knowledge smoke output; show citation in saved public model report if no live key | Policies are retrieved by tenant. Generated answers use validated source quotations; order facts come from tools. |
| 0: 55-1: 25 | MCP checker output | Both clients discover/call three read tools, read their own article and prepare a prompt. The same URI does not grant another tenant's data. |
| 1: 25-2: 10 | Agent smoke output and approval-flow diagram | The agent pauses. A distinct simulated operator approves only this synthetic fixture. Retry produces one fictional receipt. |
| 2: 10-2: 35 | CI workflow and verified release report | CI tests and builds; deployment is a separate CI-gated helper on the existing EC2 host. |
| 2: 35-3: 00 | RESULTS.md | 370 tests; 22/25 development scenarios; 16 deterministic enforcement checks. Explain one limitation and the AI-assisted implementation. |

Show the saved report filenames/time and say whether each segment is live or
recorded. Speeding up a wait is fine if labeled. Do not claim an Inspector UI demo:
the saved official Inspector proof is CLI execution over public HTTPS.

## Before publishing

Watch the full export. Confirm no `.env`, private key, token, DB URL with credentials,
clipboard popup or authentication header is visible/audible. Add the final video
URL to the root README and G4 checklist only after you actually record/review it.
The separate ten-minute no-notes walkthrough belongs in [portfolio preparation](PORTFOLIO.md).

## Cloud session end

Existing deployment needs no update for this documentation. Preserve the original
EC2 checkout path, SSM/IAM names and certificate/data volumes. Stop the existing EC2
instance from the console when finished if you do not need the live demo; do not
terminate it or delete volumes as cleanup. Disk/storage may remain while stopped.
The last user-confirmed account screen showed a free-plan end date 14 April 2027;
that historical date does not confirm today's balance or account eligibility.
Check the current billing console yourself before recording a cost claim.
