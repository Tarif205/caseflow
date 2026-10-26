# Day 12: MCP HTTP authorization, resource and prompt

Date: 26 October 2026. Implementation-first override; learning checks deferred.

Added mcp_http.py using installed MCP SDK 1.30.0's stateless Streamable HTTP
manager. The local endpoint is http://127.0.0.1:8003/mcp. Every request validates
the bearer against the DB, enforces scopes and carries identity through the SDK's
request context. Business reads recheck authorization and tenant filters.
No MCP session IDs are issued or accepted. GET/DELETE, query parameters, hostile
hosts/origins, duplicate/malformed auth and oversized bodies are rejected.

Added kb://article/{id}, returning bounded JSON with stored overlapping original
chunks for only that tenant. Added draft_support_reply(ticket, article_id), which
returns instructions plus untrusted JSON evidence without a model call or action.
Both reuse kb:read and the read-only DB boundary. Stdio remains compatible.

**343 tests passed in 27.23s**, with clean Ruff lint/format checks. Seventeen new
cases cover HTTP identity concurrency, expiry/revocation/scopes/session rejection,
resource isolation, prompt input bounds and hostile headers. Real concurrent
Northwind/Contoso SDK clients initialized, called all three tools, read their
different versions of the same article URI and prepared the prompt. Both
negotiated 2025-11-25 and received no session IDs. Evidence:
evals/results/day-12-http.json, checked_at 2026-10-26T17:31:29.749418+00:00.

The final local server runs as a hidden Uvicorn process on loopback 8003, with
ignored logs in .cache/day12-mcp-final.stdout.log and .stderr.log. An earlier
restart attempt left the old listener alive; its exact command line/PID was
verified before stopping it and restarting the final implementation. Final real
HTTP verification passed after restart. No other service was stopped.

No package, schema, credential, cloud deployment or model call was added. This is
pre-provisioned bearer authorization, not complete OAuth discovery/issuance or
third-party client consent. The existing EC2 Knowledge API and Day 10 agent/backend
releases remain unchanged. Threat table: docs/mcp-threats.md; decision record 006.

Next: user commits/pushes Day 12. Day 13 connects the agent as an MCP client and
deploys the server after local verification. No learner understanding check passed.
