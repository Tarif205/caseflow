# 007: keep the graph and adapt its reads through the locked MCP SDK

Date: 27 October 2026. Status: accepted for the local Day 13 integration.

## Context and options

The current graph already owns tool budgets, strict schemas, policy checks,
checkpointing and human approval. We need MCP discovery and calls without giving
the model control of destinations, credentials or newly advertised actions.

Options: replace the graph's tool layer with a general LangChain adapter, or
bridge its two existing read names using the already locked MCP SDK 1.30.0.
Current [LangChain documentation](https://docs.langchain.com/oss/python/langchain/mcp)
describes a beta langchain.mcp.MCPAdapter requiring langchain[mcp]>=1.4.0 and
FastMCP, replacing older langchain-mcp-adapters usage. Those packages are not
installed. The current graph does not require that agent/tool abstraction.

## Decision

Use the installed official ClientSession and streamable_http_client APIs, verified
by signature inspection and real calls. Keep the graph and its two tool names;
map them to the MCP registry explicitly. Require the expected three-tool registry,
strict input/output schema equality and read-only annotations on discovery.
Unknown/changed registries fail before execution. Annotations are contract hints;
server SQL read-only transactions remain the write boundary.

Bind principal, bearer and URL outside model control. Fresh stateless client per
read gives explicit lifecycle and avoids shared credential state. Bound the whole
sequence by remaining graph time (max 20 seconds), network response size and
strict output validation. Fail closed without direct HTTP fallback.

## Consequences and evidence

No new dependencies or model/provider changes. Discovery adds requests per read;
we accept that cost for this small demo rather than sharing authenticated sessions.
The adapter supports the project's stateless JSON-response endpoint, not arbitrary
SSE servers or OAuth discovery. Retrying a read is safe; it cannot perform refunds.

Live MCP model evaluation: 22/25 (88%); archived direct run: 21/25 (84%). This is
not evidence of a quality improvement. A paired direct-read control replayed the
same recorded model decisions and exact model-input digests: all 25 final results
matched after excluding elapsed time/diagnostics. It is not independent inference.
Durable approval is tested separately by the synthetic Docker workflow smoke.
