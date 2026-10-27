# MCP threat table and verified boundaries

Day 13 adds the agent-side MCP adapter. The complete suite now passes 370 tests.
Client registry/schema changes fail before a call; model-supplied identity/write
fields and missing scopes fail before IO. Outputs are strictly validated, response
bodies and whole read sequences are bounded, and remote plaintext URLs are
rejected. See tests/test_mcp_client.py. Eight hostile surfaces also run through
both direct and MCP adapters: 16/16 enforcement checks. No live-model injection
immunity is claimed. The Day 12 table and its original counts remain below.

Approved cloud provisioning has five additional tests for atomic/idempotent hash
creation and refusal to broaden or revive existing credentials. No plaintext
token is stored in Neon, deployment files or reports.

Day 12, 26 October 2026. Local stdio and stateless Streamable HTTP use the same
read layer. This is an application bearer-token scheme for pre-provisioned project
clients, not a complete MCP OAuth authorization-server implementation.

| Threat | Enforced boundary | Evidence in tests |
|---|---|---|
| Missing, malformed or duplicated Authorization | Exactly one bounded bearer header; reject before DB lookup | test_missing_malformed_and_duplicate_headers_never_reach_database |
| Revoked or expired credentials | Fresh DB authentication per HTTP request and per business read | test_scope_expiry_revocation_and_session_replay_fail_closed |
| A read token used for another operation | Named operation scope checked before handler and at read layer | test_resource_prompt_and_search_require_kb_scope; test_scope_expiry_revocation_and_session_replay_fail_closed |
| Caller chooses another tenant | Identity comes from stored principal, never tool arguments; SQL filters tenant | test_initialize_and_calls_are_stateless_and_tenant_bound |
| Concurrent callers share identity | SDK message context carries that request's credential, with no global caller state | test_concurrent_callers_do_not_share_token_context |
| Stolen/forged session ID carries authority | Stateless manager issues no IDs; all incoming session headers rejected | test_scope_expiry_revocation_and_session_replay_fail_closed |
| Same article URI crosses tenants | Document and chunk queries both filter authenticated tenant | test_resource_and_prompt_never_read_foreign_article |
| Foreign record existence leaks through error details | Missing and foreign records produce the same generic error | test_initialize_and_calls_are_stateless_and_tenant_bound; test_resource_and_prompt_never_read_foreign_article |
| Resource ID becomes file path or network URL | Slug-only namespace; implementation only performs scoped SQL | test_plain_resource_uri_rejects_non_namespace_inputs_before_io |
| Prompt arguments smuggle identity or grow without bound | Strict schema, required bounded ticket and article slug, no extra fields | test_prompt_arguments_are_bounded_before_any_read |
| Host/Origin abuse and DNS rebinding | Explicit host/origin allowlists before auth, plus SDK transport checks | test_invalid_arguments_host_origin_body_and_protocol_are_rejected |
| Oversized JSON, unsupported protocol or query credentials | 16 KiB body bound, SDK protocol validation, no query parameters | test_invalid_arguments_host_origin_body_and_protocol_are_rejected |
| A tool attempts a DB write | All MCP connections begin a read-only transaction; only three read tools registered | Existing Day 11 tests in tests/test_mcp_server.py and tests/test_database_connection.py |
| Sensitive request contents enter request logs | Gateway logs only generated ID, HTTP method, status and duration; Uvicorn access logs disabled in run command | Source review of mcp_http.py; not a separate log-exfiltration penetration test |

Test functions above are in tests/test_mcp_http.py unless otherwise indicated.
Parameterized cases account for 17 new tests. The complete suite passed **343
tests in 27.23s**. [Real HTTP evidence](../evals/results/day-12-http.json) also
records two concurrent SDK clients calling all three tools, reading separate
articles at the same URI, preparing prompts and receiving no session IDs.

## Limits of these checks

The transport is local at 127.0.0.1:8003. It has not been deployed or load tested.
There is no OAuth discovery, issuance, audience binding or third-party client
consent flow. Do not describe this as complete OAuth/spec authorization compliance.
GET/DELETE are rejected, so resumable SSE and stateful sessions are not supported.

The SDK can normalize URI dot segments before the resource callback. The plain
resource-validator cases demonstrate direct input rejection, not preservation of
every original wire representation. Scoped SQL and the absence of file/network
reads are the underlying boundary.

Ticket/article text remains untrusted. The prompt separates instructions and data
and performs no model call or write; this is not proof of arbitrary host-model
prompt-injection resistance. Refund permissions and human approval remain in the
existing agent/backend, outside the read-only MCP registry. Existing shared DB
credentials are application-scoped, not separate database roles per tenant.

## Primary references

- [MCP 2025-11-25 transport specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
- [MCP 2025-11-25 authorization specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)
- [Official Python SDK](https://github.com/modelcontextprotocol/python-sdk)

Installed SDK 1.30.0 negotiated 2025-11-25. The current specification checked during
Day 11 was 2026-07-28; compatibility with its newer features is not claimed.
