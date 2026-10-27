# CaseFlow decision index

These eight records explain concrete choices and their alternatives. They reflect
this portfolio's constraints, not universal recommendations.

| Decision | Chosen approach | Alternative/tradeoff |
|---|---|---|
| [001 Chunking](001-chunking.md) | 800-character windows, 120 overlap, title context for embeddings | Heading/token splits need additional rules; character windows can split words |
| [002 Grounded answers](002-grounded-answers.md) | Return validated original quotations | Free prose is more natural but harder to verify; quote presence does not prove relevance |
| [003 Agent loop](003-read-only-agent-loop.md) | Bounded plain loop as an observable baseline | General framework first would obscure the control flow |
| [004 Refund policy](004-refund-policy.md) | Pure deny-first policy over trusted facts | A model cannot grant refund authority |
| [005 MCP contract](005-local-mcp-contract.md) | Locked official SDK and fixed strict read tools | Plain functions alone do not provide protocol discovery/transport |
| [006 HTTP identity](006-stateless-mcp-http.md) | Stateless per-request scoped bearer auth | Stateful sessions/OAuth would require additional lifecycle and authorization work |
| [007 Agent adapter](007-bounded-mcp-agent-adapter.md) | Keep graph; adapt fixed reads using installed SDK | A broader adapter dependency adds unrelated abstractions; fresh discovery costs latency |
| [008 Cloud recovery](008-cloud-readiness-and-rollback.md) | Measured bounded readiness; restore previous Compose and images | Reusing new topology with old images broke recovery expectations |

For system context, see [architecture](../architecture.md). For measured outcomes,
see [results](../RESULTS.md). Historical incident reports remain unchanged.
