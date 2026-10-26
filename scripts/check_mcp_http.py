"""Real concurrent SDK clients exercise local authenticated stateless HTTP MCP."""

import hashlib
import json
from datetime import UTC, datetime

import anyio
import httpx
from dotenv import dotenv_values
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from support_copilot.config import PROJECT_ROOT
from support_copilot.mcp_server import CONTRACTS, ArticleResult


async def main():
    values = dotenv_values(PROJECT_ROOT / ".env")
    url = "http://127.0.0.1:8003/mcp"
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "url": url,
        "transport": "streamable-http",
        "stateless": True,
        "scope": "local real read-only SDK clients; no model, action or deployment",
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
                    report["sessions"].append(
                        {
                            "tenant_fixture": tenant,
                            "protocol": initialized.protocolVersion,
                            "session_id_issued": False,
                            "tools": calls,
                            "resource_read": True,
                            "article_sha256": hashlib.sha256(
                                article.model_dump_json().encode()
                            ).hexdigest(),
                            "prompt_prepared": True,
                        }
                    )

    with anyio.fail_after(90):
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
    (PROJECT_ROOT / "evals/results/day-12-http.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        anyio.run(main)
    except BaseException as exc:
        raise SystemExit(
            f"HTTP verification failed ({type(exc).__name__}); raw details withheld"
        ) from None
