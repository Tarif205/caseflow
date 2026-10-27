"""Real concurrent SDK clients exercise local authenticated stateless HTTP MCP."""

import argparse
import hashlib
import json
from datetime import UTC, datetime

import anyio
import httpx
from dotenv import dotenv_values
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from caseflow.agent_tools import safe_base_url
from caseflow.config import PROJECT_ROOT
from caseflow.mcp_server import CONTRACTS, ArticleResult


async def main(
    output="evals/results/day-12-http.json",
    endpoint="http://127.0.0.1:8003/mcp",
    timeout_seconds=90,
):
    if not 5 <= timeout_seconds <= 300:
        raise ValueError("Verification batch timeout must be 5 through 300 seconds")
    values = dotenv_values(PROJECT_ROOT / ".env")
    url = safe_base_url(endpoint)
    if not url.endswith("/mcp"):
        raise ValueError("MCP endpoint required")
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "url": url,
        "transport": "streamable-http",
        "stateless": True,
        "batch_timeout_seconds": timeout_seconds,
        "scope": "real read-only SDK clients; no model, action or deployment by this checker",
        "sessions": [],
        "complete": False,
    }

    async def check(tenant, order):
        token = values[tenant.upper() + "_MCP_API_TOKEN"]
        async with httpx.AsyncClient(
            headers={"Authorization": "Bearer " + token}, timeout=60
        ) as client:
            async with streamable_http_client(url, http_client=client) as (read, write, session_id):
                async with ClientSession(read, write) as session:
                    initialized = await session.initialize()
                    assert initialized.serverInfo.name == "caseflow-readonly"
                    assert session_id() is None
                    assert {t.name for t in (await session.list_tools()).tools} == set(CONTRACTS)
                    calls = []
                    for name, args in [
                        ("search_knowledge_base", {"query": "shipping policy", "top_k": 2}),
                        ("get_order_status", {"order_id": order}),
                        ("list_open_tickets", {"limit": 2}),
                    ]:
                        result = await session.call_tool(name, args)
                        assert not result.isError
                        CONTRACTS[name][1].model_validate(result.structuredContent)
                        calls.append({"tool": name, "status": "ok"})
                    templates = await session.list_resource_templates()
                    assert str(templates.resourceTemplates[0].uriTemplate) == "kb://article/{id}"
                    resource = await session.read_resource("kb://article/returns-policy")
                    article = ArticleResult.model_validate_json(resource.contents[0].text)
                    prompts = await session.list_prompts()
                    assert prompts.prompts[0].name == "draft_support_reply"
                    prompt = await session.get_prompt(
                        "draft_support_reply",
                        arguments={
                            "ticket": "How can I return an unused item?",
                            "article_id": "returns-policy",
                        },
                    )
                    assert "untrusted_ticket" in prompt.messages[0].content.text
                    foreign = "CT-2001" if tenant == "northwind" else "NW-1042"
                    rejected = await session.call_tool("get_order_status", {"order_id": foreign})
                    missing = await session.call_tool("get_order_status", {"order_id": "NW-9999"})
                    assert rejected.isError and missing.isError
                    assert rejected.model_dump() == missing.model_dump()
                    report["sessions"].append(
                        {
                            "tenant_fixture": tenant,
                            "protocol": initialized.protocolVersion,
                            "server_name": initialized.serverInfo.name,
                            "session_id_issued": False,
                            "tools": calls,
                            "resource_read": True,
                            "article_sha256": hashlib.sha256(
                                article.model_dump_json().encode()
                            ).hexdigest(),
                            "prompt_prepared": True,
                            "foreign_order_matches_missing_error": True,
                        }
                    )

    with anyio.fail_after(timeout_seconds):
        async with anyio.create_task_group() as group:
            group.start_soon(check, "northwind", "NW-1042")
            group.start_soon(check, "contoso", "CT-2001")
    assert len({r["article_sha256"] for r in report["sessions"]}) == 2
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        assert response.status_code == 401
    report["sessions"].sort(key=lambda row: row["tenant_fixture"])
    report["missing_auth_rejected"] = True
    report["complete"] = True
    (PROJECT_ROOT / output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--output", default="evals/results/day-12-http.json")
        parser.add_argument("--url", default="http://127.0.0.1:8003/mcp")
        parser.add_argument("--timeout-seconds", type=int, default=90)
        args = parser.parse_args()
        anyio.run(main, args.output, args.url, args.timeout_seconds)
    except BaseException as exc:
        raise SystemExit(
            f"HTTP verification failed ({type(exc).__name__}); raw details withheld"
        ) from None
