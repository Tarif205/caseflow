"""Linux dry-run harness: stub AWS/Docker/Git/curl; no network or deployment."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SHA = "a" * 40
PRIVATE_MARKER = "dry-run-private-value"

STUB = r"""
import json,os,sys
from pathlib import Path
name=Path(sys.argv[0]).name
args=sys.argv[1:]
log=Path(os.environ['HARNESS_LOG'])
with log.open('a') as f: f.write(name+' '+' '.join(args)+'\n')
if name=='git':
    if args[0]=='rev-parse': print('a'*40)
    elif args[0]=='show': print(json.dumps({'name':'support-copilot-agent','services':{'support-agent':{'image':'old-agent:bbbbbbbbbbbb','depends_on':['mock-backend']},'mock-backend':{'image':'old-backend:bbbbbbbbbbbb'}}}))
elif name=='aws': print('dry-run-private-value')
elif name=='awk': print('2048')
elif name=='curl':
    if any('api.github.com' in a for a in args):
        print(json.dumps({'workflow_runs':[{'id':1,'head_sha':'a'*40,'head_branch':'main','event':'push','run_number':1,'status':'completed','conclusion':os.getenv('HARNESS_CI','success'),'html_url':'https://github.com/example/run/1'}]}))
    elif os.getenv('HARNESS_FAIL')=='public' and any('/mcp/ready' in a and a.startswith('https:') for a in args): sys.exit(22)
    else: print('{"status":"ready"}')
elif name=='sudo':
    if args and args[0].startswith('--preserve-env='): args=args[1:]
    os.execvp(args[0],args)
elif name=='docker':
    if args[0]=='inspect':
        if args[-1].endswith('mcp-server-1'):
            print('false' if 'Running' in args[2] else 'failed-mcp:cccccccccccc')
            sys.exit(0)
        print('old-agent:bbbbbbbbbbbb' if args[-1].endswith('support-agent-1') else 'old-backend:bbbbbbbbbbbb')
    if args[0]=='compose' and 'up' in args and os.getenv('HARNESS_FAIL')=='compose' and '--no-deps' not in args:
        sys.exit(42)
"""


def exercise(source, *, failed="", ci="success", manual=False):
    with tempfile.TemporaryDirectory(prefix="mcp-deploy-safety-") as temp:
        root = Path(temp)
        (root / "scripts").mkdir()
        (root / ".cache").mkdir()
        (root / "bin").mkdir()
        shutil.copyfile(source, root / "scripts/deploy_mcp_ec2.sh")
        (root / "compose.agent-aws.yaml").write_text("services: {}\n")
        original = "old.example { reverse_proxy 127.0.0.1:8001 }\n"
        proxy = root / ".cache/Caddyfile.agent"
        proxy.write_text(original)
        for name in ("git", "aws", "curl", "sudo", "docker", "awk"):
            stub = root / "bin" / name
            stub.write_text("#!" + sys.executable + "\n" + STUB)
            stub.chmod(0o755)
        log = root / "commands.log"
        env = {
            **os.environ,
            "PATH": str(root / "bin") + os.pathsep + os.environ["PATH"],
            "HARNESS_LOG": str(log),
            "HARNESS_FAIL": failed,
            "HARNESS_CI": ci,
        }
        command = ["bash", str(root / "scripts/deploy_mcp_ec2.sh"), SHA, "16-178-30-70.sslip.io"]
        result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        assert PRIVATE_MARKER not in output
        if not log.exists():
            raise RuntimeError("Dry-run failed before command stubs: " + output)
        events = log.read_text()
        assert PRIVATE_MARKER not in events
        if ci != "success":
            assert result.returncode != 0 and proxy.read_text() == original
            assert "aws " not in events and "docker build" not in events and " up " not in events
            return
        if failed:
            assert (
                result.returncode == (42 if failed == "compose" else 22)
                and proxy.read_text() == original
            )
            assert "--no-deps --wait mock-backend support-agent" in events
            assert "stop mcp-server" in events
        else:
            assert result.returncode == 0 and "handle /mcp {" in proxy.read_text()
            assert "handle_path /agent/*" in proxy.read_text()
            assert "reverse_proxy 127.0.0.1:8001" in proxy.read_text()
        rollback = root / ".cache" / ("day13-rollback-" + SHA[:12])
        images = (rollback / "images.yaml").read_text()
        assert "old-agent:bbbbbbbbbbbb" in images and "old-backend:bbbbbbbbbbbb" in images
        previous = json.loads((rollback / "compose.previous.yaml").read_text())
        assert not (
            rollback / "had-mcp"
        ).exists()  # A stopped failed attempt is not the old release.
        assert "healthcheck" not in previous["services"]["support-agent"]
        assert "mcp-server" not in previous["services"]
        if failed:
            assert "compose.previous.yaml" in events
        if manual:
            result = subprocess.run(
                command + ["--rollback"], env=env, capture_output=True, text=True, timeout=30
            )
            assert result.returncode == 0 and proxy.read_text() == original
            assert PRIVATE_MARKER not in result.stdout + result.stderr


def main():
    if os.name != "posix":
        raise ValueError("Run in the Linux verification container")
    source = Path(__file__).resolve().parent / "deploy_mcp_ec2.sh"
    subprocess.run(["bash", "-n", str(source)], check=True)
    exercise(source, manual=True)
    exercise(source, failed="compose")
    exercise(source, failed="public")
    exercise(source, ci="failure")
    print(
        json.dumps(
            {
                "complete": True,
                "checks": [
                    "bash_syntax",
                    "success_and_route_preservation",
                    "automatic_rollback",
                    "explicit_rollback",
                    "failed_ci_refused_before_secrets_or_updates",
                    "no_credentials_in_output",
                ],
                "scope": "stubbed Linux harness only; no AWS/Docker/network mutations",
            }
        )
    )


if __name__ == "__main__":
    main()
