"""Pinned official Inspector HTTP checks; credentials stay out of argv/files/reports."""

import argparse
import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from dotenv import dotenv_values

from caseflow.agent_tools import safe_base_url
from caseflow.config import PROJECT_ROOT
from caseflow.mcp_server import CONTRACTS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8003/mcp")
    parser.add_argument(
        "--token-env",
        choices=["NORTHWIND_MCP_API_TOKEN", "NORTHWIND_WORKER_API_TOKEN"],
        default="NORTHWIND_MCP_API_TOKEN",
    )
    parser.add_argument(
        "--output", type=Path, default=PROJECT_ROOT / "evals/results/day-13-local-inspector.json"
    )
    args = parser.parse_args()
    url = safe_base_url(args.url)
    if not url.endswith("/mcp"):
        raise ValueError("MCP endpoint required")
    token = dotenv_values(PROJECT_ROOT / ".env").get(args.token_env) or ""
    node = shutil.which("node")
    if not node:
        raise ValueError("Node required")
    npm = (
        [node, str(Path(node).parent / "node_modules/npm/bin/npm-cli.js")]
        if os.name == "nt"
        else [shutil.which("npm") or "npm"]
    )
    prefix = npm + [
        "exec",
        "--offline",
        "--yes",
        "--package=node@24.22.1",
        "--package=@modelcontextprotocol/inspector@2.12.0",
        "--",
        "node",
        str(PROJECT_ROOT / "scripts/inspector_http.mjs"),
        "--server-url",
        url,
    ]
    env = {
        **os.environ,
        "CASEFLOW_INSPECTOR_TOKEN": token,
        "npm_config_cache": "G:/npm-cache" if os.name == "nt" else str(PROJECT_ROOT / ".cache/npm"),
    }

    def invoke(options):
        result = subprocess.run(
            prefix + options,
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=90,
        )
        if result.returncode:
            raise RuntimeError("Inspector HTTP failed; raw output withheld")
        return json.loads(result.stdout)["result"]

    definitions = invoke(["--method", "tools/list"])["tools"]
    assert {t["name"] for t in definitions} == set(CONTRACTS)
    calls = []
    for name, arguments in [
        ("search_knowledge_base", {"query": "shipping policy", "top_k": 2}),
        ("get_order_status", {"order_id": "NW-1042"}),
        ("list_open_tickets", {"limit": 2}),
    ]:
        result = invoke(
            [
                "--method",
                "tools/call",
                "--tool-name",
                name,
                "--tool-args-json",
                json.dumps(arguments),
            ]
        )
        assert not result.get("isError")
        CONTRACTS[name][1].model_validate(result["structuredContent"])
        calls.append({"tool": name, "status": "ok"})
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "url": url,
        "transport": "streamable-http",
        "inspector_version": "2.12.0",
        "node_version": "24.22.1",
        "protocol_era": "legacy",
        "calls": calls,
        "complete": True,
        "scope": "official CLI HTTP check; no UI screenshot or action calls",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(
            f"Inspector HTTP failed ({type(exc).__name__}); raw output withheld"
        ) from None
