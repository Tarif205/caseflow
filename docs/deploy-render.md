# Optional zero-budget fallback: Render + Neon

Status on 22 October 2026: configuration prepared, **not deployed**. Use this route
if AWS signup needs a card or the user chooses the PRD fallback. `render.yaml`
declares one explicitly Free Docker web service, with automatic deployments off.
It declares no database, persistent disk or paid resource.

## Limits checked before preparation

[Render's free-service documentation](https://render.com/docs/free) states that free
web services sleep after 15 idle minutes, lose local files on restart, and share
750 free instance hours per workspace per month. They support managed TLS.
[Compute plans](https://render.com/docs/compute-plans) list 512 MB RAM for Free.
Our image has not yet been verified on that resource limit: if it cannot run, keep
deployment pending and reduce resource use; do not upgrade to a paid instance.
The first `/ready` or search downloads embedding weights into an ephemeral cache.
Cold starts and repeated model downloads are expected limitations. Use Neon for
persistent data rather than Render's expiring free Postgres database.

The schema follows the [current Blueprint reference](https://render.com/docs/blueprint-spec).
Provider account access and actual service creation remain pending. Do not assume
signup is card-free for every account; stop if payment is requested.

## Prepare the hosted database after confirming the host account

In the Neon console, select a dedicated empty project database or branch for this
fictional demo. Check the Free plan and connection target. The existing ignored
`.env` contains `NEON_DATABASE_URL`; confirm that it points to the intended demo
database before proceeding. Do not overwrite unrelated existing data. No remote
schema or data has been changed by the assistant during deployment preparation.

In VS Code's PowerShell terminal at `G:\support-copilot`, the following captures
the connection string directly into a process variable, without displaying it:

```powershell
cd G:\support-copilot
$env:DATABASE_URL = (& .venv\Scripts\python.exe -c "from dotenv import dotenv_values; from psycopg.conninfo import conninfo_to_dict; u=dotenv_values('.env').get('NEON_DATABASE_URL',''); c=conninfo_to_dict(u); assert c.get('host','').endswith('.neon.tech') and c.get('sslmode') in {'require','verify-ca','verify-full'}, 'Set the intended Neon TLS URL first'; print(u)")
if ($LASTEXITCODE -ne 0) { throw 'Neon settings check failed; stop here.' }
uv run --frozen caseflow init-db
if ($LASTEXITCODE -ne 0) { throw 'Schema initialization failed; stop here.' }
uv run --frozen caseflow seed-corpus
if ($LASTEXITCODE -ne 0) { throw 'Corpus initialization failed; stop here.' }
uv run --frozen caseflow provision-token --tenant northwind --scope kb:read --scope kb:write --env-name NORTHWIND_API_TOKEN
if ($LASTEXITCODE -ne 0) { throw 'Northwind token provisioning failed; stop here.' }
uv run --frozen caseflow provision-token --tenant contoso --scope kb:read --env-name CONTOSO_API_TOKEN
if ($LASTEXITCODE -ne 0) { throw 'Contoso token provisioning failed; stop here.' }
Remove-Item Env:DATABASE_URL
```

These commands write the schema, tenant rows, fictional articles and token hashes
to that selected database. Existing token values remain only in `.env`; provisioning
reuses them and registers their hashes in the selected database. The seed command
preserves existing articles. Always remove the process override when finished;
open a fresh terminal if a failure interrupts these steps before cleanup.

## Create the Free service

1. The user reviews, commits and pushes the project, excluding `.env`. Wait for
   GitHub Actions to pass. Render builds from the pushed revision, not local files.
2. Sign in to Render. Create a Blueprint from the repository and review `render.yaml`.
   Confirm it creates exactly one **Free** web service. Automatic deploys are off;
   creating the Blueprint still performs its initial deployment.
3. Enter `DATABASE_URL` from the intended Neon connection string and `LLM_API_KEY`
   from the existing Groq key directly into Render's secret environment settings.
   Do not place API bearer tokens in the service environment; only their hashes
   are needed in the database. Do not paste secret values into chat.
4. Review the Free selection and all resource details, then create the service.
   Do not select a disk, paid compute plan or paid workspace upgrade. The command
   listens on port 10000, with one worker, matching the manifest's `PORT`.
5. After the build finishes, use its assigned HTTPS URL. `/health` indicates only
   process liveness. Wait for `/ready` to finish the initial embedding download;
   inspect memory and safe logs if it fails. No migrations run in the web process.

## Verify the actual deployment

Replace the example hostname below with the URL assigned by Render, in the same
project's PowerShell terminal. The script reads bearer tokens locally from `.env`:

```powershell
uv run --frozen python scripts/smoke_knowledge.py --base-url https://YOUR-SERVICE.onrender.com --output evals/results/day-05-api-smoke.json
```

Success requires health/readiness 200, unauthenticated request 401, each tenant's
own article results, order-specific refusal and a real cited warranty answer.
Keep the artifact only after success; never fabricate a deployment URL or result.
Record the deployed revision, service URL, actual memory behavior and restart
check in the Day 5 journal. Keep demo tokens private, especially Northwind's write
token. This is a small authenticated demo; no rate-limiting guarantee is claimed.

Rollback uses an earlier known-good deploy in Render; database changes require
their own recovery plan. Delete the service when it is no longer needed. Recheck
usage and free terms before demos. Public deployment and Gate G1 remain pending
until the checks above have actually succeeded.
