#!/usr/bin/env bash
# Run on the existing Ubuntu EC2 host after the user commits/pushes the release.
set -euo pipefail
cd "$(dirname "$0")/.."
expected_commit="${1:?Pass the reviewed commit id}"
public_host="${2:?Pass the current IP-encoded sslip.io hostname}"
[[ "$expected_commit" =~ ^[0-9a-f]{7,40}$ ]]
[[ "$public_host" =~ ^[0-9]+(-[0-9]+){3}\.sslip\.io$ ]]
git diff --quiet
git pull --ff-only origin main
actual_commit="$(git rev-parse HEAD)"
[[ "$actual_commit" == "$expected_commit"* ]]
export COPILOT_IMAGE_TAG="${actual_commit:0:12}"
export KNOWLEDGE_API_URL="https://$public_host"
DATABASE_URL="$(aws ssm get-parameter --region ap-southeast-2 --name /support-copilot/DATABASE_URL --with-decryption --query Parameter.Value --output text --no-cli-pager)"
LLM_API_KEY="$(aws ssm get-parameter --region ap-southeast-2 --name /support-copilot/LLM_API_KEY --with-decryption --query Parameter.Value --output text --no-cli-pager)"
export DATABASE_URL LLM_API_KEY
trap 'unset DATABASE_URL LLM_API_KEY' EXIT
[[ -n "$DATABASE_URL" && -n "$LLM_API_KEY" ]]
sudo docker build -f services/mock-backend/Dockerfile -t "caseflow-backend:$COPILOT_IMAGE_TAG" .
sudo docker build -f services/support-agent/Dockerfile -t "caseflow-agent:$COPILOT_IMAGE_TAG" .
# Never print docker compose config: its expanded output contains credentials.
compose=(sudo --preserve-env=DATABASE_URL,LLM_API_KEY,COPILOT_IMAGE_TAG,KNOWLEDGE_API_URL docker compose -f compose.agent-aws.yaml)
"${compose[@]}" config --quiet
"${compose[@]}" run --rm --no-deps support-agent caseflow init-agent
"${compose[@]}" run --rm --no-deps support-agent caseflow seed-mock
"${compose[@]}" up -d
curl --retry 12 --retry-all-errors --retry-delay 2 --max-time 15 -fsS http://127.0.0.1:8002/ready
mkdir -p .cache
cat > .cache/Caddyfile.agent <<EOF
$public_host {
    handle_path /agent/* {
        reverse_proxy 127.0.0.1:8002
    }
    handle {
        reverse_proxy 127.0.0.1:8001
    }
}
EOF
sudo docker run --rm -v "$PWD/.cache/Caddyfile.agent:/etc/caddy/Caddyfile:ro" caddy:2.11.7 caddy validate --config /etc/caddy/Caddyfile
if sudo docker container inspect support-copilot-proxy-before-agent >/dev/null 2>&1; then
    sudo docker exec support-copilot-proxy caddy reload --config /etc/caddy/Caddyfile
else
    sudo docker stop support-copilot-proxy
    sudo docker rename support-copilot-proxy support-copilot-proxy-before-agent
    if ! sudo docker run -d --name support-copilot-proxy --network host --restart unless-stopped --memory 256m \
        --log-opt max-size=5m --log-opt max-file=2 \
        -v support-copilot-caddy-data:/data -v support-copilot-caddy-config:/config \
        -v "$PWD/.cache/Caddyfile.agent:/etc/caddy/Caddyfile:ro" \
        caddy:2.11.7 caddy run --config /etc/caddy/Caddyfile; then
        sudo docker rm -f support-copilot-proxy
        sudo docker rename support-copilot-proxy-before-agent support-copilot-proxy
        sudo docker start support-copilot-proxy
        exit 1
    fi
fi
curl --retry 8 --retry-all-errors --retry-delay 2 --max-time 15 -fsS "https://$public_host/agent/health"
printf '\nAgent health verified. Run the authenticated approval smoke before claiming G2.\n'
