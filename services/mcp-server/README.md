# Read-only MCP server: Day 11 local stdio

MCP lets a client discover tool schemas and call them through a standard protocol.
This server wraps the existing retrieval/order/ticket reads. It does not call a
chat model, draft replies, approve actions or execute refunds.

```text
Inspector or SDK client -> stdio JSON-RPC -> MCP server -> read-only Postgres
                                               +----> cached CPU query embedding
```

The calling application is the host; its MCP client manages initialization and
requests. The server advertises capabilities, validates calls and returns typed
data. A plain function alone does not provide that discovery/transport contract.
Learning checks remain deferred; this paragraph is not a passed explain-back.

## Tools and exact contract

| Tool | Purpose | Inputs | Output | Scope | Read-only |
|---|---|---|---|---|---|
| search_knowledge_base | Ranked help-center passages | query: nonblank string, max 1000; top_k: integer 1-5, default 3 | results: up to 5 hits with id, document_id, title, source, text, finite score | kb:read | Yes |
| get_order_status | Status/tracking and policy-check facts | order_id: NW- or CT- plus 4-8 digits | id, customer_id, status, total_cents, currency, tracking_number | orders:read | Yes |
| list_open_tickets | Bounded open tickets | limit: integer 1-20, default 10 | tickets: id, customer_id, text, status=open | tickets:read | Yes |

No tool accepts tenant, credential, URL, approval or write arguments. Extra fields,
boolean/string counts, invalid ids and bounds are rejected. Order customer/amount
facts are explicitly included for the later agent policy adapter; customer names,
order notes, placement date, token hashes and internal tenant columns are omitted.
Ticket/article content is untrusted data, never instructions or permissions.

The credential is bound by the trusted local launcher. Existing token validation
and read-scope checks are reused per call, with tenant from the stored principal.
Every downstream query filters by it. Missing/foreign orders share the same
not_found error. Errors return generic codes, not SQL, driver errors or secrets.
The DB helper opens these calls in a read-only transaction; annotations are just
client hints and are not the enforcement boundary.

## Current version compatibility

- Locked Python MCP SDK: **1.30.0**. Real SDK client negotiated **2025-11-25**.
- Current specification checked 26 October 2026: **2026-07-28**.
- Inspector **2.12.0** runs with explicit **legacy** protocol era to interoperate
  with the locked SDK. This does not claim modern-spec feature support.
- Existing system Node **22.16.0** is below Inspector's >=22.19.0 requirement.
  Inspector runs with isolated **Node 24.22.1** in G:\npm-cache. System Node was
  verified unchanged. No Python dependencies were added or upgraded.

The low-level official SDK is used deliberately: strict Pydantic input validation
and whitelisted output schemas stay explicit. The installed FastMCP helper's
generated argument model does not forbid extras by default; silently dropping a
tenant argument would hide a bad caller contract.

## Run and verify in this workspace

Use **Windows PowerShell at G:\support-copilot**, with local Docker Postgres
running and the already seeded corpus/mock data. New local read-only credentials
NORTHWIND_MCP_API_TOKEN and CONTOSO_MCP_API_TOKEN were generated into ignored .env;
their hashes are stored only in local Postgres. No values are printed or copied
into client config. No Neon schema, cloud token or deployed service was changed.

Real SDK stdio check for both tenants:

```powershell
.venv\Scripts\python.exe scripts/check_mcp_stdio.py
```

Expected: complete=true, three successful calls per tenant, negotiated protocol,
blocked foreign reads, rejected tenant injection and no write tool.

The pinned Inspector/runtime are already cached on G:. Run its real CLI checks:

```powershell
.venv\Scripts\python.exe scripts/check_mcp_inspector.py
```

Expected: complete=true and all three calls status=ok. Saved evidence:
[SDK sessions](../../evals/results/day-11-stdio.json),
[Inspector CLI](../../evals/results/day-11-inspector.json).
These are real stdio calls, not mocked transport or a browser screenshot.

For a fresh cache, this downloads only temporary pinned tooling to G: and prints
help; it does not update the system Node installation:

```powershell
$env:npm_config_cache='G:\npm-cache'
npm.cmd exec --yes --package=node@24.22.1 --package=@modelcontextprotocol/inspector@2.12.0 -- mcp-inspector --cli --help
```

npm can warn that its parent system Node is old while resolving packages. The
verification script separately asserts the actual isolated runtime is v24.22.1.
Use --offline after the cache is populated; no paid service is involved.

To list tools directly through Inspector:

```powershell
$env:npm_config_cache='G:\npm-cache'
npm.cmd exec --offline --yes --package=node@24.22.1 --package=@modelcontextprotocol/inspector@2.12.0 -- mcp-inspector --cli --protocol-era legacy --format json --quiet --method tools/list G:\support-copilot\.venv\Scripts\python.exe -m support_copilot.mcp_server
```

To select Contoso in a local stdio session, set the **credential name**, not its
value, before launching the server/client:

```powershell
$env:MCP_TOKEN_ENV='CONTOSO_MCP_API_TOKEN'
.venv\Scripts\python.exe -m support_copilot.mcp_server
```

Running the server alone appears silent while waiting for JSON-RPC stdin. That
is expected; it opens no HTTP port. Stop it with Ctrl+C. SDK logs/errors use stderr;
stdout is reserved for protocol messages. The checker launches/cleans its own
subprocesses, so do not also start a separate server for those checks.

If recreating local read credentials after an empty database setup:

```powershell
.venv\Scripts\python.exe -m support_copilot.cli provision-token --tenant northwind --scope kb:read --scope orders:read --scope tickets:read --env-name NORTHWIND_MCP_API_TOKEN
.venv\Scripts\python.exe -m support_copilot.cli provision-token --tenant contoso --scope kb:read --scope orders:read --scope tickets:read --env-name CONTOSO_MCP_API_TOKEN
```

Keep DATABASE_URL on the local development database for Day 11. These are trusted
admin commands that generate tokens; do not add empty token placeholders first.

## Verification and next step

**326 tests passed in 27.02s**, including 18 new schema/projection/scope/tenant/read-only
checks and the existing Postgres integration suite. Inspector listed and called
all tools. The SDK client independently initialized and called them for both tenants.
No hosted/local chat model run, refund, write tool, HTTP transport, resource,
prompt or MCP deployment was added for Day 11.

Day 12 adds Streamable HTTP authorization/header/session coverage, the article
resource and draft prompt. Day 13 connects the agent as an MCP client and deploys
the server. Existing EC2 services remain on their verified Day 10 releases.

References: [current specification](https://modelcontextprotocol.io/specification),
[official Python SDK](https://github.com/modelcontextprotocol/python-sdk),
[Inspector documentation](https://modelcontextprotocol.io/docs/tools/inspector).
