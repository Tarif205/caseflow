# Day 11: local read-only MCP server

Date: 26 October 2026. Implementation-first override; learning checks deferred.

Added the official SDK low-level stdio server with three bounded tools, strict
schemas and projected outputs. Reused current credential/scope/tenant checks and
added a read-only option to the shared DB connection helper; default behavior of
other services is unchanged. No model arguments can set identity or permissions.

Generated separate Northwind/Contoso MCP read credentials into ignored .env; only
hashes in local Postgres. Existing credentials and cloud services were untouched.
The stdio loader reads only required .env values, without loading unrelated LLM
keys into its subprocess environment. No credential appears in argv or reports.

Checked installed SDK 1.30.0 interfaces and current official docs. The SDK client
negotiated 2025-11-25; current specification is 2026-07-28. Inspector 2.12.0 was
run in legacy mode using isolated Node 24.22.1 on G:, while global Node remained
22.16.0. Initial un-escalated npm metadata access failed; the permitted network
request and cached runtime completed normally. No system upgrade/Python dep change.

Real SDK stdio sessions initialized, listed and called all three tools for both
tenants; foreign reads, injected tenant args and unavailable write tool rejected.
Official Inspector CLI independently listed/called all three tools. Saved
day-11-stdio.json and day-11-inspector.json; no browser UI/screenshot claim.

**326 tests passed in 27.02s**, including 18 new checks. Tests cover schema/size/
type constraints, projected fields, closed ticket exclusion, tenant scoping,
generic foreign/missing errors, read scopes, live revocation and actual read-only
transaction enforcement. Lint and formatting clean. New tool table/setup commands
are in services/mcp-server/README.md; decision record 005 documents SDK choice.

No chat model call, refund, new HTTP service, resource, prompt or cloud deployment
for Day 11. Existing EC2 API/agent releases preserved. User commits/pushes.
Next: Day 12 HTTP auth/scopes/isolation coverage plus article resource/draft prompt.
