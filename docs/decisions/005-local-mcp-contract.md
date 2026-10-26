# 005: Explicit read contracts on a local stdio MCP server

Date: 26 October 2026. Day 11 implemented; HTTP/resource/prompt/deployment pending.

## Decision

Expose only search_knowledge_base, get_order_status and list_open_tickets using
the locked official Python MCP SDK's low-level Server. Advertise strict input and
output JSON schemas; manually validate extra=forbid before any read, then project
only explicit output fields. All queries run in read-only transactions with tenant
and read scopes derived from a credential bound outside model arguments.

## Alternatives

| Option | Benefit | Tradeoff |
|---|---|---|
| Keep plain Python functions | Simple | No MCP discovery, initialization or client interoperability |
| FastMCP default function decorator | Less boilerplate | Installed generated argument model does not forbid extras by default |
| Low-level SDK plus explicit Pydantic models | Exact schemas/errors/projection and normal MCP clients | More explicit dispatch code |

Choose the third. A tenant argument must be rejected rather than silently ignored.
No custom JSON-RPC implementation or dependency upgrade is needed. ReadOnlyHint
is advisory; actual SQL scope and transaction permissions enforce the boundary.

## Consequences and verification

Local stdio uses scoped credentials from ignored .env and authenticates each read.
This is not HTTP bearer middleware, OAuth or a remote multi-user server. Day 12
adds that request boundary before anything is publicly hosted.

SDK 1.30.0 negotiated 2025-11-25 in the real SDK check; the current specification
is 2026-07-28. Use Inspector 2.12.0's legacy era instead of claiming modern-spec
features. Its required runtime is supplied by pinned Node 24.22.1 on G:, preserving
the machine's existing Node 22.16.0 and the locked Python environment.

Both SDK and Inspector clients listed/called all three real tools. Tests verify
schema bounds, extra argument rejection, exact outputs, tenant separation, scopes,
revocation and read-only SQL. Revisit transport/version choices on Day 12/13 with
tests; do not introduce resources, prompts or remote authorization out of order.
