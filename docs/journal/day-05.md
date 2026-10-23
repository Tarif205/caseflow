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
