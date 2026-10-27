"""Validate cloud Compose/Caddy locally using dummy values; never start the stack."""

import json
import os
import re
import subprocess

from caseflow.config import PROJECT_ROOT


def command(args, *, env=None):
    result = subprocess.run(
        args, cwd=PROJECT_ROOT, env=env, capture_output=True, text=True, timeout=90
    )
    if result.returncode:
        raise RuntimeError("Deployment configuration check failed; expanded output withheld")
    return result.stdout


def main():
    host = "16-178-30-70.sslip.io"
    env = {
        **os.environ,
        "DATABASE_URL": "postgresql://validation-only.invalid/app",
        "LLM_API_KEY": "configuration-validation-only",
        "COPILOT_IMAGE_TAG": "validation",
        "KNOWLEDGE_API_URL": "https://" + host,
        "MCP_PUBLIC_HOST": host,
    }
    cfg = json.loads(
        command(
            [
                "docker",
                "compose",
                "--env-file",
                ".env.example",
                "-f",
                "compose.agent-aws.yaml",
                "config",
                "--format",
                "json",
            ],
            env=env,
        )
    )
    assert cfg["name"] == "support-copilot-agent"
    mcp = cfg["services"]["mcp-server"]
    assert mcp["image"] == "caseflow-mcp:validation"
    assert len(mcp["ports"]) == 1
    assert (
        mcp["ports"][0]["host_ip"] == "127.0.0.1"
        and str(mcp["ports"][0]["published"]) == "8003"
        and mcp["ports"][0]["target"] == 8000
    )
    assert int(mcp["mem_limit"]) == 512 * 1024 * 1024
    # Cloud DB round trips measured >4s. Allow a real DB readiness request to
    # complete, with a larger outer Docker deadline and startup grace period.
    for service in ("mcp-server", "support-agent"):
        check = cfg["services"][service]["healthcheck"]
        match = re.search(r"timeout=(\d+)", " ".join(check["test"]))
        assert match and int(match[1]) >= 10
        assert float(check["timeout"].removesuffix("s")) > int(match[1])
        assert float(check["start_period"].removesuffix("s")) > 0
    assert set(mcp["environment"]["MCP_ALLOWED_HOSTS"].split(",")) == {
        host,
        "mcp-server",
        "localhost",
        "127.0.0.1",
    }
    assert (
        cfg["services"]["support-agent"]["environment"]["MCP_SERVER_URL"]
        == "http://mcp-server:8000/mcp"
    )
    assert not cfg["services"]["mock-backend"].get("ports")
    assert cfg["volumes"]["mcp-embeddings"]["external"] is True
    assert cfg["volumes"]["mcp-embeddings"]["name"] == "support-copilot-embeddings"
    source = (PROJECT_ROOT / "scripts/deploy_mcp_ec2.sh").read_text(encoding="utf-8")
    match = re.search(r"cat > \.cache/Caddyfile\.mcp-candidate <<EOF\n(.*?)\nEOF", source, re.S)
    if match is None:
        raise ValueError("Caddy template missing")
    candidate = match[1].replace("$public_host", host) + "\n"
    path = PROJECT_ROOT / ".cache/Caddyfile.day13-validation"
    path.parent.mkdir(exist_ok=True)
    path.write_text(candidate, encoding="utf-8", newline="\n")
    prefix = [
        "docker",
        "run",
        "--rm",
        "-v",
        str(path) + ":/etc/caddy/Caddyfile:ro",
        "caddy:2.11.7",
        "caddy",
    ]
    command(prefix + ["validate", "--config", "/etc/caddy/Caddyfile"])
    adapted = json.loads(
        command(prefix + ["adapt", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"])
    )
    text = json.dumps(adapted)
    for route in ("/mcp", "/mcp/*", "/agent/*"):
        assert json.dumps(route) in text
    for upstream in ("127.0.0.1:8001", "127.0.0.1:8002", "127.0.0.1:8003"):
        assert upstream in text
    print(
        json.dumps(
            {
                "complete": True,
                "checks": [
                    "compose_parsed_with_dummy_values",
                    "loopback_mcp_port",
                    "fixed_internal_agent_url",
                    "explicit_hosts",
                    "existing_cache_volume",
                    "caddy_validated",
                    "mcp_agent_and_knowledge_routes_preserved",
                ],
                "scope": "local configuration only; no stack startup, secrets or cloud change",
            }
        )
    )


if __name__ == "__main__":
    main()
