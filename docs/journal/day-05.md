# Day 5 deployment preparation

Date: 22 October 2026. Assistant preparation under the workflow override.
Learning checks remain deferred.

Prepared `docs/deploy-aws.md`, the optional `render.yaml` Free-service manifest,
and `docs/deploy-render.md` with database setup and HTTPS smoke verification.
No AWS CLI, local profile/credentials or Render API key were found. The existing
Neon setting is present; its value was not displayed or copied into another file.

Current official AWS and Render documentation was consulted. Account-specific
eligibility, signup and the final plan selection still need verification. AWS
account status was requested from the user while preparing the files.

Local manifest validation passed: YAML parses, exactly one explicitly Free service
is declared, redeploys are manual, the Dockerfile exists, and no secret values,
database resources or disks are declared. `git diff --check` passed. Provider-side
Blueprint validation and the 512 MB hosted runtime have not been tested.

No remote database was changed, resource provisioned, repository pushed or public
service deployed. The previous 143-test result concerns the Day 4 code. Deployment
configuration validation is separate from a successful hosted runtime. CI, public
smoke evidence, restart recovery, the full API refusal evaluation and Gate G1 remain
pending. Do not start Day 6 on the assumption that this preparation passed G1.

Next step: establish an eligible Free AWS account without a payment card, or select
the PRD's free fallback. Follow the chosen deployment guide using the reviewed,
user-pushed revision, then record real deployment evidence.

## Progress on 23 October 2026 (supersedes the preparation status above)

- Screenshot confirms Free plan, $100 credits and expiry 14 April 2027; no upgrade.
- User launched Ubuntu 24.04 LTS x86, t3.small, one 20 GiB gp3 volume in Sydney.
  SSH is My IP only; public IP enabled; inbound HTTP/HTTPS remain closed.
- Instance screenshot shows Running and 3/3 checks passed. SSH login succeeded
  after restricting Windows permissions on the downloaded .pem file. No private
  key contents were shared. Added .pem/.key ignore rules to prevent accidental
  inclusion in later commits.
- User supplied successful Docker hello-world output and Compose version
  2.40.3+ds1-0ubuntu1~24.04.1. Docker uses Ubuntu packages and is enabled at boot.
- Application code remains uncommitted locally. Next: user commit/push, GitHub CI,
  then deploy that revision with Neon and hosted-model secrets. No cloud API,
  public smoke result or completed Gate G1 is claimed. No assistant commit/push.

## Subsequent verified progress and learning documentation

The user committed/pushed `3d0bd84`; their GitHub Actions screenshot confirms the
`checks` run passed. User cloned that revision onto EC2 and supplied successful
image-build output: `support-copilot-knowledge:3d0bd84`, image id `04d288243eea`.
The legacy builder warning did not block the build. No cloud application container
has been started or public answer verified. The read-only Neon inspection was
requested but its results have not yet been provided.

The user requested a full explanation and study roadmap before continuing.
Created `docs/PROJECT_EXPLAINED.md` and `docs/LEARNING_ROADMAP.md`, linking actual
code/evidence, official references and relevant videos/search terms. These docs
distinguish CI from manual deployment, current functionality from planned features,
and guided execution from independent mastery. No new cloud action was taken.

## Neon initialization and pooling compatibility fix

User SQL results confirmed neondb, vector 0.8.6 and initially no public tables.
The user's CLI initialization partially succeeded (schema transaction committed)
before a later connection failed. Read-only diagnostics isolated Neon's rejection
of statement_timeout passed as a startup option. database.connect now sets the
10-second timeout transaction-locally after connecting. A real local Postgres
regression covers pooler rejection, actual query cancellation and savepoint recovery.
Local verification: 144 tests passed, lint/format passed.

Assistant repeated the authorized initialization against Neon successfully: ready,
vector 0.8.6, dimension 384, two tenant rows and zero documents; query timeout 10s.
No stored credential values were changed, printed or copied into another file.
Corpus/token-hash provisioning, hosted inference, HTTPS and public smoke remain
pending. The EC2 image at 3d0bd84 needs rebuilding after the user commits/pushes
this fix and CI passes. No assistant commit/push.

User subsequently supplied successful hosted corpus seed output: 15 Northwind
documents/30 chunks and 3 Contoso documents/6 chunks, using BGE small and baseline
800/120 character windows. User token provisioning output confirms Northwind
read/write and Contoso read hashes registered in Neon. No token values were shared.
Next: publish the tested connection fix, obtain passing CI, update/rebuild EC2,
then configure the runtime securely and perform actual deployed API checks.

## Stop/resume record — 24 October 2026

User-pushed `531d7c4` passed CI by screenshot. The user updated EC2 to that
revision and rebuilt the image successfully: `df9d03e1bb95`, tag 531d7c4.
User created the database parameter (Standard/SecureString visible in screenshot)
and reported creating the model-key parameter in Parameter Store. No secret values
were shared. IAM role creation/access testing remains pending.

User explicitly chose to stop and resume tomorrow from IAM, then confirmed the
EC2 instance was stopped, not terminated. No further deployment work should occur
until resumed. Disk/image persist; credit consumption for storage remains possible.
Resume with the EC2 role wizard, and start the existing Sydney instance when needed,
checking its new public IP and status before SSH. API runtime/HTTPS/public smoke
and G1 remain incomplete. No assistant commit/push.

## Resumed deployment — 25 October 2026

User created the EC2 IAM role and parameter-specific read policy, confirmed role
attachment by screenshot, and restarted the instance. Current public IP is
16.178.30.70. Code revision/image match 531d7c4/df9d03e1bb95. AWS CLI 2.38.5
was installed; STS confirms the instance role and SecureString retrieval/decryption
works for both named parameters without displaying their values.

API container is now running privately on EC2 loopback port 8001, with 768 MB
limit, restart unless-stopped, rotated logs and persistent model cache. Runtime
credentials were passed by environment name rather than embedded in shell command
arguments or a copied .env file. Docker's privileged metadata still retains the
container environment; shell unsetting does not remove it from the running service.

User ran the real laptop smoke script over an SSH tunnel. Saved artifact:
`evals/results/day-05-ec2-ssh-smoke.json`, timestamp
2026-10-25T16:39:35.869938+00:00. All checks passed: health/readiness, missing token,
tenant searches, order refusal and a real cited warranty quote. This establishes
the EC2 -> Neon/embeddings/Groq -> validated-answer path through private access,
not public HTTPS. Certificate/proxy/public smoke, restart recovery and remaining
G1 checks are pending. Next: public TCP 80/443 security-group rules and Caddy TLS
using a verified free demo hostname. No assistant commit/push.
## Public HTTPS milestone — 26 October 2026 (Asia/Dhaka)

User saved TCP 80/443 Anywhere-IPv4 ingress while preserving SSH /32. Caddy
2.11.7 container `support-copilot-proxy` was started with host networking,
256 MB limit, persistent certificate/config volumes and restart unless-stopped.
User logs confirm Let's Encrypt certificate obtained for 16-178-30-70.sslip.io.
Proxy forwards to EC2 loopback 8001; raw API/DB ports remain unexposed.

Public smoke passed: `evals/results/day-05-public-https-smoke.json`, checked_at
2026-10-25T20:39:18.174217+00:00. All seven checks passed with normal certificate
verification: health/readiness, missing-token rejection, both tenant searches,
order-specific refusal and real warranty evidence with source citation. This is
the actual deployed HTTPS path. No rate-limiting, production hardening or broad
answer-quality result is inferred from it.

Pending: memory/swap measurement, restart recovery with post-restart public checks,
full API refusal evaluation and remaining G1 review. No complete G1/Day 5 claim.
Current hostname depends on the public IP; update and verify it after IP changes.
No assistant commit/push.

## Restart, resource and actual refusal evidence — 26 October 2026

User-supplied Docker stats show 348.9 MiB API memory and 11.14 MiB proxy memory.
The host had 1.1 GiB available of 1.9 GiB total and no swap configured. This is
a post-request snapshot, not a measured peak or concurrency/load test.

Manual `docker restart` recovered the same API container. The first curl received
a transient connection reset; a subsequent check confirmed Up and /ready success.
The user reran public smoke successfully with a real warranty quotation. Evidence:
`evals/results/day-05-public-after-restart.json`. Crash/reboot auto-recovery is
not claimed just from a manual restart and configured restart policy.

Added a repeatable API-level ten-case refusal evaluator. Actual public run returned
10/10 refusals, no HTTP errors, 8 no_evidence and 2 record_lookup_required. These
were deterministic pre-model gates; no model-decline/invented-answer behavior was
needed on these ten cases. Dataset is synthetic/in-sample; answerable acceptance
and semantic faithfulness require separate evaluation. Evidence:
`evals/results/day-05-public-refusals.json`. The script stops on HTTP/contract
errors, counts against the full planned denominator and cannot call a partial
or provider-error run a passing gate.

Validation: nine new tests passed; all 99 non-integration tests passed with 54
integration tests deselected, and Ruff lint/format passed. The attempted full run
was interrupted after DB setup timeouts; local Docker Desktop is stopped. Prior
144-test verification concerns the earlier code. Fresh CI for evaluator/evidence
and explicit clean-clone Compose runtime verification are pending. No completed
G1 claim or assistant commit/push. No server code change was required by the
operator-only evaluation tooling.

## Technical closeout — 26 October 2026

User pushed 7c2f4fe and reports CI green. Docker Desktop is running again; full
local suite passed **153 tests in 8.46s**, including database integration.
Fresh committed local Git clone with no .env/working-tree files passed Compose
build/up and health/readiness with brand-new DB/cache volumes. Port-only override
and a separate project avoided touching the existing development stack. Generated
temporary read tokens authenticated both tenants' real searches; source isolation
and expected 15/30 + 3/6 corpus counts passed. A separate wrong-password application
returned safe health 200/readiness 503. No hosted model calls or secrets were used
by the clean-stack check. Evidence: evals/results/day-05-clean-clone.json.

Temporary test containers/network/volumes were removed after verification; original
development/cloud services and data were preserved. Technical G1 review is in
docs/gates/G1-verification.md. Learning explain-back remains deferred. Latest
evidence/report await user commit/push. Next implementation is Day 6; no agent
work was started in this closeout. No assistant commit/push.
