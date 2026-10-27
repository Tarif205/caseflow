# CaseFlow rename and compatibility map

Date: 27 October 2026. The product is **CaseFlow**, formerly Support Copilot.
The public repository is **caseflow**. This is a rename of the
existing project, with its history, tenant data and approval rules preserved.

## Completed in source

- Python distribution, import package and CLI: caseflow; source: src/caseflow.
- Imports in scripts/tests, package resource loading and service entrypoints.
- Current Markdown documentation, API titles, MCP server name and CaseFlow_PRD.md.
- New Docker builds use caseflow-knowledge, caseflow-backend and caseflow-agent.
- Dockerfiles use CASEFLOW_PROJECT_ROOT. COPILOT_PROJECT_ROOT remains a fallback
  for existing deployment environments. Both assistant contracts stay synchronized.

Historical journals, decisions, gate reports, evaluation JSON and Word documents
retain the names actually used at the time. They are evidence/archives, not the
current run instructions. Follow current service READMEs for caseflow imports and
commands. Historical image tags remain accurate for the currently deployed release.

## GitHub repository: completed

The user renamed the existing GitHub repository to **caseflow**. The agent updated
origin to https://github.com/Tarif205/caseflow.git and verified access with
git ls-remote origin HEAD (8e0a543c4860261b3fc98e09c27d456f400c2aa0 at this check).
Fetch/push remotes both use the new URL. Commands for reference:

```powershell
git remote set-url origin https://github.com/Tarif205/caseflow.git
git remote -v
```

Expected: origin fetch/push both show Tarif205/caseflow.git. Keep the existing
repository; do not create a second empty repository or delete the original.
The user still makes the commit and push for the reviewed source rename.
GitHub documents the rename and remote-update procedure in its
[official repository rename guide](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository).

## Local folder: completed and verified

The user moved the workspace to G:\caseflow and recreated .venv there. The old
G:\support-copilot directory no longer exists. Verified Python executable,
caseflow package and PROJECT_ROOT all resolve under G:\caseflow; the CLI help
works and the virtual environment prompt is caseflow. The previous environment
is retained in ignored .venv-before-caseflow. Current runnable documentation now
uses the new path. Historical evidence retains the paths used at its creation.

## Existing identifiers intentionally retained

| Identifier | Reason |
|---|---|
| Local Postgres user/database copilot, test DB copilot_test | Existing state and test safety allowlist; changing names requires an explicit DB migration |
| Compose project support-copilot | Owns current local containers, network, dbdata and embedding-cache volumes |
| AWS Compose project support-copilot-agent | Owns deployed agent/backend containers; prevents a second conflicting stack |
| COPILOT_IMAGE_TAG | Existing Compose/deploy-script release contract, now selecting CaseFlow image names |
| /support-copilot/DATABASE_URL and /support-copilot/LLM_API_KEY | Existing encrypted SSM parameters and IAM resource permissions |
| support-copilot-ec2-role, key filename and instance Name | Operational identifiers, independent of product branding |
| Existing proxy/container/certificate-volume names | Preserve the working routes, TLS certificates and rollback procedure |
| Existing EC2 checkout ~/support-copilot | Moving it can invalidate the proxy's absolute bind mount; leave until a coordinated deployment |
| Langfuse project and old traces | Historical observations; no telemetry history rewritten |

None of these names is visible as the new product branding. A database or Docker
volume rename is not required to use CaseFlow. Blind replacement can create an
empty database, lose access to secrets or start duplicate containers. New releases
will carry CaseFlow labels while these stable deployment identifiers keep their
existing values. No cloud rename, migration or deployment has happened in this step.

Day 13 agent/MCP integration remains the next feature after the rename is saved.
Learning checks remain deferred.

## Verification on 27 October 2026

- Frozen uv sync rebuilt caseflow 0.1.0 and removed the old distribution; no
  dependency versions changed. The local caseflow CLI help runs.
- All 343 tests passed in 29.90 seconds, including Postgres integration and
  separate-process durable approval checks. Ruff lint and formatting passed.
- Real stdio and concurrent HTTP checks assert server_name=caseflow-readonly and
  verify both tenants. New evidence: evals/results/caseflow-rename-stdio.json and
  evals/results/caseflow-rename-http.json. Historical evidence was not overwritten;
  the checker scripts now accept --output to choose another report filename.
- All three caseflow-*:rename Docker images built. Network-disabled disposable
  containers verified the packaged schema, /app root and caseflow CLI entrypoint.
  Current running service containers were not replaced.
- Docker Desktop was initially closed, causing the first test attempt's DB
  connection errors. Started Desktop and the existing DB volume, then reran the
  complete suite successfully. No database or volume was recreated.
- Local MCP Uvicorn now runs caseflow.mcp_http:app on loopback 8003; ignored logs
  are .cache/caseflow-rename-mcp.stdout.log and .stderr.log.
