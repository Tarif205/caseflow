#!/usr/bin/env bash
# Retain the previous entrypoint; the reviewed Day 13 helper owns deployment.
set -euo pipefail
exec bash "$(dirname "$0")/deploy_mcp_ec2.sh" "$@"
