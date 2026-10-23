# Day 5: AWS deployment preparation

Status on 23 October 2026: **EC2 prepared; application not deployed**. The user
confirmed the Free plan ($100 credits, expiry 14 April 2027 or credit exhaustion),
launched Ubuntu 24.04 LTS x86 on t3.small with 20 GiB gp3 in Sydney, and connected
over SSH restricted to My IP. All 3 instance checks passed. User-provided output
confirms Docker hello-world success and Compose 2.40.3. HTTP/HTTPS inbound remain
closed. No AWS CLI, local profile or credentials are configured on the laptop.
GitHub CI passed for user-pushed commit `3d0bd84`; that revision was cloned and its
API image built on EC2 (`support-copilot-knowledge:3d0bd84`, id `04d288243eea`).
The API container has not started there. Neon inspection and schema/tenant setup
are now verified, but corpus/token hashes, secure runtime setup, the public API
endpoint and Gate G1 remain pending. A subsequently fixed Neon-pool compatibility
bug requires a new user commit/push and rebuilt image before cloud startup.

The signup section below records the initial eligibility checks. Signup is now
complete; do not repeat it. The commit, push, CI, clone and image build are also
complete. Next: finish Neon corpus/tokens, publish/rebuild the connection fix,
configure runtime secrets and HTTPS, start
the service and verify it. Keys remain outside the repository.

## First action: establish account eligibility

Open https://aws.amazon.com/free/ and choose account signup. Select **Free plan**,
never Paid. The [current AWS FAQ](https://aws.amazon.com/free/free-tier-faqs/)
says a payment method is not required for most new customers, but eligibility and
signup flows vary. The Free plan lasts up to six months or until its credits run
out; this is not unlimited free hosting. Do not upgrade it.

The user has explicitly chosen zero budget and no payment card. If signup requests
a card, stop that route and use [the fallback](deploy-render.md). Do not enter
payment information, choose a paid support plan, or launch an instance before the
account's plan and eligible resources are confirmed. No resource was provisioned
while preparing these notes.

## AWS rollout checklist after signup

These are pending steps, not a record of an executed deployment. Exact instance
choices and console commands depend on the eligible account/region and must be
checked there before provisioning.

1. Confirm the console says Free plan. Record its expiry, credit balance and
   eligible EC2 instance types. Enable root MFA; use a non-root identity for work.
   Check which budget/alert facilities the account permits without upgrading.
2. Select an eligible instance with at least 2 GB RAM if available. Do not assume
   a familiar instance type is free. Include storage and public network usage in
   the credit review. Do not provision NAT gateways, load balancers, paid registries
   or other extra infrastructure for this demo.
3. Restrict SSH to the user's current public IP. Keep Postgres and the application
   port private; expose HTTPS through a configured reverse proxy. Establish a free
   hostname/certificate path before sending a bearer token over the public network.
4. Install Docker using the official instructions for the selected OS. Deploy only
   the Knowledge API image, pointed at Neon and hosted inference. Local Compose is
   for development and includes public demo database credentials: do not publish it.
5. Use standard Parameter Store parameters only if allowed in this Free account;
   store the database URL and model key securely. Give the instance role access
   only to the required parameters. Do not bake secrets into images or commands,
   commit environment files, or paste secrets into chat. Do not print decrypted
   values while loading the service's process environment.
6. Prepare a dedicated empty Neon database/branch with the same 384-dimensional
   embedding model. See the preparation section in [deploy-render.md](deploy-render.md),
   which applies to either host. Check the target before applying the schema.
7. Configure non-root execution, one Uvicorn worker, a restart policy, log rotation
   and an embedding cache on the instance. Keep a previous working image tag for
   rollback. Measure memory with a real request rather than assuming readiness
   proves the model fits.
8. Over HTTPS, verify `/health`, `/ready` and the authenticated smoke script. Restart
   the container and check recovery. Verify safe database-failure behavior in a
   disposable test configuration rather than changing the live database password.
9. Record the URL, image/revision, instance/region, plan/expiry, measured memory,
   smoke artifact, restart result and remaining G1 requirements. Remove unused
   resources and recheck the account's billing/credit page after the session.

Git commits and pushes remain with the user. CI must pass after the push; it has
not run on GitHub yet. Learning checks remain deferred under the workflow override.
