# Read-only MCP server: local stdio and Streamable HTTP

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

## Day 11 verification

**326 tests passed in 27.02s**, including 18 new schema/projection/scope/tenant/read-only
checks and the existing Postgres integration suite. Inspector listed and called
all tools. The SDK client independently initialized and called them for both tenants.
No hosted/local chat model run, refund, write tool, HTTP transport, resource,
prompt or MCP deployment was added for Day 11.

## Day 12: authenticated Streamable HTTP

The same three tools are now available at http://127.0.0.1:8003/mcp. Each HTTP
request supplies its own Authorization bearer header. The server checks the
credential against Postgres, then each read checks its scope and tenant again.
It uses pre-provisioned project tokens; it does **not** implement OAuth discovery,
token issuance or third-party-client authorization.

```text
SDK client -> authenticated POST /mcp -> request-bound identity -> scoped SQL
                                                        +----> CPU embeddings
```

The server is stateless: no MCP session ID is issued, and any supplied
Mcp-Session-Id is rejected. Authority cannot be transferred through a session ID.
GET and DELETE return 405 after authentication; there is no resumable SSE channel.
LangGraph's durable approval checkpoints remain separate from this transport.

In **PowerShell at G:\support-copilot**, start the local server only if port 8003
is not already running:

```powershell
.venv\Scripts\python.exe -m uvicorn support_copilot.mcp_http:app --host 127.0.0.1 --port 8003 --no-access-log
```

Expected: Uvicorn listening on 127.0.0.1:8003. It stays running in that terminal;
Ctrl+C stops it. A background instance was started during Day 12 verification.
In a second PowerShell terminal, run:

```powershell
.venv\Scripts\python.exe scripts/check_mcp_http.py
```

Expected: complete=true, three successful calls per tenant, resource_read=true,
prompt_prepared=true and session_id_issued=false. The checker reads the two local
MCP credentials from ignored .env without putting values in argv or reports.
It runs concurrent real SDK HTTP clients and saves
[HTTP evidence](../../evals/results/day-12-http.json). Different article hashes
show that the same URI resolves to each caller's separate tenant content.

Clients send application/json and the SDK's JSON/SSE Accept headers. Requests
are bounded to 16 KiB. Missing, expired, revoked or malformed credentials get
401; missing operation scopes get 403. Token query parameters are rejected.
Host and Origin are checked before authentication. Defaults allow localhost and
127.0.0.1 hosts, and Inspector origins http://localhost:6274 and
http://127.0.0.1:6274. Non-browser clients can omit Origin. For other hosts, set
MCP_ALLOWED_HOSTS (comma-separated bare hostnames) and MCP_ALLOWED_ORIGINS
(comma-separated exact origins) in the **process environment** before starting
Uvicorn. Wildcards are rejected. These two settings are not loaded from .env.
Public exposure/deployment remains Day 13 work.

### Article resource and prompt

| Capability | Contract | Scope |
|---|---|---|
| Resource template kb://article/{id} | JSON id, title, source, chunks containing id, position, text | kb:read |
| Prompt draft_support_reply | Required ticket (nonblank, max 4000 characters) and article_id (lowercase slug, max 100) | kb:read |

The article resource reads only stored chunks for the authenticated tenant.
It returns original overlapping chunks rather than reconstructing a full article.
It permits at most 64 chunks, 4000 characters per chunk and 64 KiB serialized JSON.
The resource ID is a document slug, never a file path or external URL. Missing and
foreign articles share the same generic error; resources/list does not enumerate
tenant documents. Extra prompt arguments are rejected.

The prompt returns a trusted instruction prefix followed by JSON containing the
untrusted ticket and article. It asks a future host model for a cited draft and
human review. Preparing the prompt calls no model and performs no action.
It does not establish that a future host model resists every prompt injection.

**343 tests passed in 27.23s**, with lint and formatting clean. Day 12 adds 17
cases covering HTTP authorization, concurrent identity isolation, resource/prompt
scope checks, bounded inputs and hostile headers. See the
[threat table](../../docs/mcp-threats.md). No dependencies, cloud services, schema,
tokens or model calls were added for Day 12. Learning checks remain deferred.

Day 13 connects the agent as an MCP client and deploys the server. Existing EC2
services remain on their verified Day 10 releases; MCP is verified locally only.

References: [current specification](https://modelcontextprotocol.io/specification),
[official Python SDK](https://github.com/modelcontextprotocol/python-sdk),
[Inspector documentation](https://modelcontextprotocol.io/docs/tools/inspector).
