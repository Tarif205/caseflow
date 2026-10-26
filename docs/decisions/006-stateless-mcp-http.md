# 006: stateless MCP HTTP with request-bound credentials

Date: 26 October 2026. Status: accepted for the local project transport.

## Context

The Day 11 MCP server exposes only short read operations. HTTP adds concurrent
callers, so a credential bound once at process startup cannot identify all clients.
A reusable session ID must not become another caller's authority.

## Decision

Use the installed official SDK's StreamableHTTPSessionManager with stateless=True
and JSON responses. Authenticate every request against Postgres, require the
operation's read scope, reject incoming session IDs and issue none. Allow POST
only after authentication. No resumable SSE or persistent session state is needed.

Carry the verified bearer in that request's ASGI scope. The MCP read adapter obtains
it from the SDK message's request_context.request, including in threaded reads.
Each business read authenticates again and takes the tenant from the principal.
Do not use a global credential, a mutable current-user field or a session cache.
The stdio adapter retains its explicitly selected launcher credential.

Add bounded JSON bodies, explicit Host/Origin allowlists and generic failures.
Reuse the same read-only SQL layer for tools, article resources and the prompt.
Prompt preparation returns instructions/evidence and calls no model or action.

## Consequences and evidence

Concurrent HTTP tests and two real SDK clients verified separate tenant content.
Tests also reject expired/revoked credentials, missing scopes and session headers.
343 total tests passed; day-12-http.json records the real transport check.

These are pre-provisioned project bearer tokens, not a complete OAuth server or
third-party consent flow. Deployment and an agent client remain Day 13 work.
Durable human approvals continue to live in LangGraph/Postgres independently.
Learning checks remain deferred.
