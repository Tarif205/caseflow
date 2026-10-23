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
