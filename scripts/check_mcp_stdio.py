"""Real SDK stdio initialization/list/calls for both local read credentials."""

import argparse
import json
import os
import sys
from datetime import UTC, datetime

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from caseflow.config import PROJECT_ROOT
from caseflow.mcp_server import CONTRACTS


async def check(output="evals/results/day-11-stdio.json"):
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "transport": "stdio",
        "sdk_version": "1.30.0",
        "current_specification_at_check": "2026-07-28",
        "scope": "local real reads only; no hosted model, writes or deployment",
        "sessions": [],
        "complete": False,
    }
    for tenant, order, foreign in [
        ("northwind", "NW-1042", "CT-2001"),
        ("contoso", "CT-2001", "NW-1042"),
    ]:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "caseflow.mcp_server"],
            cwd=str(PROJECT_ROOT),
            env={"MCP_TOKEN_ENV": tenant.upper() + "_MCP_API_TOKEN"},
        )
        with open(os.devnull, "w") as errors:
            with anyio.fail_after(90):
                async with stdio_client(params, errlog=errors) as (read, write):
                    async with ClientSession(read, write) as session:
                        init = await session.initialize()
                        assert init.serverInfo.name == "caseflow-readonly"
                        tools = (await session.list_tools()).tools
                        assert {t.name for t in tools} == set(CONTRACTS)
                        cases = [
                            ("search_knowledge_base", {"query": "shipping policy", "top_k": 2}),
                            ("get_order_status", {"order_id": order}),
                            ("list_open_tickets", {"limit": 2}),
                        ]
                        checks = []
                        for name, args in cases:
                            result = await session.call_tool(name, args)
                            assert not result.isError and result.structuredContent is not None
                            expected = CONTRACTS[name][1]
                            expected.model_validate(result.structuredContent)
                            checks.append(
                                {
                                    "tool": name,
                                    "status": "ok",
                                    "output_fields": sorted(result.structuredContent),
                                }
                            )
                        missing = await session.call_tool("get_order_status", {"order_id": foreign})
                        assert (
                            missing.isError
                            and json.loads(missing.content[0].text)["code"] == "not_found"
                        )
                        extra = await session.call_tool(
                            "list_open_tickets", {"tenant_id": "foreign"}
                        )
                        assert (
                            extra.isError
                            and json.loads(extra.content[0].text)["code"] == "invalid_arguments"
                        )
                        unknown = await session.call_tool("execute_refund", {})
                        assert unknown.isError
                        report["sessions"].append(
                            {
                                "tenant_fixture": tenant,
                                "negotiated_protocol": init.protocolVersion,
                                "server_name": init.serverInfo.name,
                                "tools": checks,
                                "foreign_read_blocked": True,
                                "injected_tenant_rejected": True,
                                "write_tool_unavailable": True,
                            }
                        )
    report["complete"] = True
    path = PROJECT_ROOT / output
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--output", default="evals/results/day-11-stdio.json")
        anyio.run(check, parser.parse_args().output)
    except BaseException as exc:
        raise SystemExit(
            f"Stdio verification failed ({type(exc).__name__}); raw details withheld"
        ) from None
