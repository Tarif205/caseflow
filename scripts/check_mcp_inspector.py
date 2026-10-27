"""Pinned official Inspector CLI against the real local stdio server."""

import json
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from caseflow.config import PROJECT_ROOT
from caseflow.mcp_server import CONTRACTS

INSPECTOR = "@modelcontextprotocol/inspector@2.12.0"
NODE = "node@24.22.1"


def main():
    node = shutil.which("node")
    if not node:
        raise ValueError("Node required")
    if os.name == "nt":
        npm = [node, str(Path(node).parent / "node_modules/npm/bin/npm-cli.js")]
    else:
        npm = [shutil.which("npm") or "npm"]
    base = npm + ["exec", "--offline", "--yes", f"--package={NODE}", f"--package={INSPECTOR}", "--"]
    env = {
        **os.environ,
        "npm_config_cache": "G:/npm-cache" if os.name == "nt" else str(PROJECT_ROOT / ".cache/npm"),
        "MCP_TOKEN_ENV": "NORTHWIND_MCP_API_TOKEN",
    }
    runtime = subprocess.run(
        base + ["node", "--version"],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert runtime.returncode == 0 and runtime.stdout.strip() == "v24.22.1"
    prefix = base + [
        "mcp-inspector",
        "--cli",
        "--protocol-era",
        "legacy",
        "--format",
        "json",
        "--quiet",
    ]
    target = [sys.executable, "-m", "caseflow.mcp_server"]

    def invoke(options):
        result = subprocess.run(
            prefix + options + target,
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=90,
        )
        if result.returncode:
            raise RuntimeError("Inspector call failed; raw stderr withheld")
        return json.loads(result.stdout)["result"]

    definitions = invoke(["--method", "tools/list"])["tools"]
    assert {t["name"] for t in definitions} == set(CONTRACTS)
    calls = []
    for name, args in [
        ("search_knowledge_base", {"query": "shipping policy", "top_k": 2}),
        ("get_order_status", {"order_id": "NW-1042"}),
        ("list_open_tickets", {"limit": 2}),
    ]:
        result = invoke(
            ["--method", "tools/call", "--tool-name", name, "--tool-args-json", json.dumps(args)]
        )
        assert not result.get("isError")
        value = result["structuredContent"]
        CONTRACTS[name][1].model_validate(value)
        calls.append({"tool": name, "status": "ok", "output_fields": sorted(value)})
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "inspector_version": "2.12.0",
        "isolated_node_version": "24.22.1",
        "system_node_unchanged": True,
        "protocol_era": "legacy",
        "transport": "stdio",
        "listed_tools": [t["name"] for t in definitions],
        "calls": calls,
        "complete": True,
        "scope": "local read-only Inspector CLI; no UI or deployment claim",
    }
    (PROJECT_ROOT / "evals/results/day-11-inspector.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(
            f"Inspector verification failed ({type(exc).__name__}); raw details withheld"
        ) from None
