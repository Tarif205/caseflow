#!/usr/bin/env bash
# Approved Day 13 migration on the existing EC2 host. No new cloud resources.
set -euo pipefail
cd "$(dirname "$0")/.."
expected_commit="${1:?Pass the full reviewed commit SHA}"
public_host="${2:?Pass the current IP-encoded sslip.io hostname}"
mode="${3:-deploy}"
[[ "$expected_commit" =~ ^[0-9a-f]{40}$ ]]
[[ "$public_host" =~ ^[0-9]+(-[0-9]+){3}\.sslip\.io$ ]]
[[ "$mode" == deploy || "$mode" == --rollback ]]
[[ "$(git rev-parse HEAD)" == "$expected_commit" ]]
[[ -z "$(git status --porcelain)" ]]

export COPILOT_IMAGE_TAG="${expected_commit:0:12}"
export KNOWLEDGE_API_URL="https://$public_host"
export MCP_PUBLIC_HOST="$public_host"
rollback_dir=".cache/day13-rollback-$COPILOT_IMAGE_TAG"
proxy_config=".cache/Caddyfile.agent"
[[ -s "$proxy_config" ]]
sudo docker container inspect support-copilot-proxy >/dev/null
sudo docker volume inspect support-copilot-embeddings >/dev/null

if [[ "$mode" == deploy ]]; then
    # Public GitHub data only; refuse missing/pending/failed CI before any mutation.
    ci_json="$(curl -fsS --connect-timeout 10 --max-time 30 -H 'Accept: application/vnd.github+json' \
        "https://api.github.com/repos/Tarif205/caseflow/actions/workflows/ci.yml/runs?head_sha=$expected_commit&event=push&per_page=20")"
    python3 -c '
import json,sys
rows=[r for r in json.load(sys.stdin).get("workflow_runs",[]) if r.get("head_sha")==sys.argv[1] and r.get("head_branch")=="main" and r.get("event")=="push"]
if not rows: raise SystemExit("No release CI run found; deployment refused")
r=max(rows,key=lambda r:(r["run_number"],r.get("run_attempt",1)))
if r.get("status")!="completed" or r.get("conclusion")!="success": raise SystemExit("Release CI is not successful; deployment refused")
print(json.dumps({k:r[k] for k in ("id","head_sha","status","conclusion","html_url")}))
' "$expected_commit" <<< "$ci_json"
    available_mb="$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)"
    [[ "$available_mb" -ge 600 ]] || { printf 'Insufficient available memory; deployment refused.\n' >&2; exit 1; }
fi

DATABASE_URL="$(aws ssm get-parameter --region ap-southeast-2 --name /support-copilot/DATABASE_URL --with-decryption --query Parameter.Value --output text --no-cli-pager)"
LLM_API_KEY="$(aws ssm get-parameter --region ap-southeast-2 --name /support-copilot/LLM_API_KEY --with-decryption --query Parameter.Value --output text --no-cli-pager)"
export DATABASE_URL LLM_API_KEY
trap 'unset DATABASE_URL LLM_API_KEY' EXIT
[[ -n "$DATABASE_URL" && -n "$LLM_API_KEY" ]]
compose=(sudo --preserve-env=DATABASE_URL,LLM_API_KEY,COPILOT_IMAGE_TAG,KNOWLEDGE_API_URL,MCP_PUBLIC_HOST docker compose -f compose.agent-aws.yaml)
"${compose[@]}" config --quiet  # Expanded config contains credentials; never print it.

restore_previous() {
    local failed=0
    [[ -s "$rollback_dir/images.yaml" && -s "$rollback_dir/Caddyfile.agent" && -s "$rollback_dir/compose.previous.yaml" ]] || return 1
    local restore=(sudo --preserve-env=DATABASE_URL,LLM_API_KEY,COPILOT_IMAGE_TAG,KNOWLEDGE_API_URL,MCP_PUBLIC_HOST docker compose --project-directory "$PWD" -f "$rollback_dir/compose.previous.yaml" -f "$rollback_dir/images.yaml")
    # Preserve the bind-mounted inode by copying contents rather than renaming it.
    cat "$rollback_dir/Caddyfile.agent" > "$proxy_config" || failed=1
    sudo docker exec support-copilot-proxy caddy reload --config /etc/caddy/Caddyfile || failed=1
    if [[ -s "$rollback_dir/had-mcp" ]]; then
        "${restore[@]}" up -d --no-deps --wait mcp-server mock-backend support-agent || failed=1
    else
        "${restore[@]}" up -d --no-deps --wait mock-backend support-agent || failed=1
        "${compose[@]}" stop mcp-server || failed=1
    fi
    curl --retry 10 --retry-all-errors --retry-delay 2 --max-time 15 -fsS http://127.0.0.1:8002/ready || failed=1
    return "$failed"
}
if [[ "$mode" == --rollback ]]; then
    restore_previous
    printf '\nPrevious proxy and agent images restored; data and certificate volumes preserved.\n'
    exit 0
fi

sudo docker build -f services/mock-backend/Dockerfile -t "caseflow-backend:$COPILOT_IMAGE_TAG" .
sudo docker build -f services/support-agent/Dockerfile -t "caseflow-agent:$COPILOT_IMAGE_TAG" .
sudo docker build -f services/mcp-server/Dockerfile -t "caseflow-mcp:$COPILOT_IMAGE_TAG" .
mkdir -p "$rollback_dir"
if [[ ! -s "$rollback_dir/images.yaml" ]]; then
    old_agent="$(sudo docker inspect --format '{{.Config.Image}}' support-copilot-agent-support-agent-1)"
    old_backend="$(sudo docker inspect --format '{{.Config.Image}}' support-copilot-agent-mock-backend-1)"
    old_mcp=""
    old_mcp_running="$(sudo docker inspect --format '{{.State.Running}}' support-copilot-agent-mcp-server-1 2>/dev/null || true)"
    if [[ "$old_mcp_running" == true ]]; then
        old_mcp="$(sudo docker inspect --format '{{.Config.Image}}' support-copilot-agent-mcp-server-1)"
    fi
    [[ "$old_agent" =~ ^[a-zA-Z0-9_./:@-]+$ && "$old_backend" =~ ^[a-zA-Z0-9_./:@-]+$ ]]
    # Restore the previous topology too: new health/dependency rules must not
    # be applied to old images during rollback. Release images use commit tags.
    previous_commit="${old_agent##*:}"
    [[ "$previous_commit" =~ ^[0-9a-f]{12}$ ]]
    git show "$previous_commit:compose.agent-aws.yaml" > "$rollback_dir/compose.previous.yaml"
    cat "$proxy_config" > "$rollback_dir/Caddyfile.agent"
    printf 'services:\n  support-agent:\n    image: %s\n  mock-backend:\n    image: %s\n' "$old_agent" "$old_backend" > "$rollback_dir/images.yaml"
    if [[ -n "$old_mcp" ]]; then
        [[ "$old_mcp" =~ ^[a-zA-Z0-9_./:@-]+$ ]]
        printf '  mcp-server:\n    image: %s\n' "$old_mcp" >> "$rollback_dir/images.yaml"
        printf 'yes\n' > "$rollback_dir/had-mcp"
    fi
fi
cat > .cache/Caddyfile.mcp-candidate <<EOF
$public_host {
    handle /mcp {
        reverse_proxy 127.0.0.1:8003
    }
    handle_path /mcp/* {
        reverse_proxy 127.0.0.1:8003
    }
    handle_path /agent/* {
        reverse_proxy 127.0.0.1:8002
    }
    handle {
        reverse_proxy 127.0.0.1:8001
    }
}
EOF
sudo docker run --rm -v "$PWD/.cache/Caddyfile.mcp-candidate:/etc/caddy/Caddyfile:ro" caddy:2.11.7 caddy validate --config /etc/caddy/Caddyfile

rollback_on_error() {
    local status=$?
    trap - ERR
    printf 'Deployment failed; restoring previous proxy and agent images.\n' >&2
    restore_previous || printf 'Automatic rollback incomplete; inspect the saved rollback directory.\n' >&2
    exit "$status"
}
trap rollback_on_error ERR
# Keep the current agent running until the new read service proves ready.
"${compose[@]}" up -d --wait mcp-server
"${compose[@]}" up -d --wait mock-backend support-agent
curl --retry 12 --retry-all-errors --retry-delay 2 --max-time 15 -fsS http://127.0.0.1:8003/ready
curl --retry 12 --retry-all-errors --retry-delay 2 --max-time 15 -fsS http://127.0.0.1:8002/ready
cat .cache/Caddyfile.mcp-candidate > "$proxy_config"
sudo docker exec support-copilot-proxy caddy reload --config /etc/caddy/Caddyfile
curl --retry 8 --retry-all-errors --retry-delay 2 --max-time 15 -fsS "https://$public_host/mcp/ready"
curl --retry 8 --retry-all-errors --retry-delay 2 --max-time 15 -fsS "https://$public_host/agent/health"
curl --retry 8 --retry-all-errors --retry-delay 2 --max-time 15 -fsS "https://$public_host/health"
trap - ERR
printf '\nMCP/agent health verified. Run authenticated public MCP, Inspector and workflow checks before claiming G3.\n'
