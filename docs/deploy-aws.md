# Day 5: AWS deployment preparation

## Current verified milestone — 26 October 2026

The Knowledge API runs on EC2 from image `support-copilot-knowledge:531d7c4`
(id df9d03e1bb95). Neon has the corpus and API token hashes. The instance role
can read/decrypt the two standard Parameter Store values; no static AWS access
keys were installed. The API binds only to EC2 loopback port 8001.

Both the SSH-tunnel smoke and the **public HTTPS smoke passed** with a real cited
warranty answer. Public URL: https://16-178-30-70.sslip.io. Evidence:
[private check](../evals/results/day-05-ec2-ssh-smoke.json),
[public check](../evals/results/day-05-public-https-smoke.json). Public run timestamp
is 2026-10-25T20:39:18.174217+00:00 (26 October in Asia/Dhaka).
All seven checks passed with normal TLS verification, including both tenants,
missing-token rejection, order-specific refusal and verified source quotations.
Current public IP is 16.178.30.70 and can change after stop/start.

Public TCP 80/443 are open; SSH retains its restricted /32 source. Keep API 8001
and Postgres 5432 unexposed. Caddy 2.11.7 forwards public HTTPS to EC2 loopback
8001. User logs confirm Let's Encrypt certificate issuance for the hostname. The
[DNS provider](https://sslip.io/) supports IP-encoded hostnames and the
[Caddy docs](https://caddyserver.com/docs/quick-starts/reverse-proxy) describe
automated HTTPS for publicly reachable names. No paid domain/load balancer is needed
for this demo setup. Manual restart recovered and post-restart public smoke passed:
[evidence](../evals/results/day-05-public-after-restart.json). A resource snapshot
showed API 348.9 MiB, proxy 11.14 MiB, 1.1 GiB host memory available and no swap.
This does not measure peak memory or prove automated crash/reboot recovery.

The actual API refusal gate passed 10/10 development cases with no HTTP errors:
[results](../evals/results/day-05-public-refusals.json). Eight were no_evidence and
two record_lookup_required, all before generation. This is API refusal evidence,
not held-out quality, answerable acceptance or model faithfulness evidence.
Repeat from local PowerShell with:

```powershell
.venv\Scripts\python.exe scripts/check_refusals.py --base-url https://16-178-30-70.sslip.io --output evals/results/day-05-public-refusals.json
```

The evaluator sends ten synthetic unanswerable questions sequentially. It can
consume up to ten hosted generations if the service's earlier gates allow them.
Do not repeatedly run it without a reason. A provider/HTTP error stops evaluation
and prevents a passing gate, rather than counting the failure as a refusal.

### G1 technical closeout

Technical checks are verified; original learning explain-back remains deferred.
See [the full review](gates/G1-verification.md) and
[fresh-clone evidence](../evals/results/day-05-clean-clone.json). User reports
green CI for 7c2f4fe and the full local suite now passes 153 tests. Latest evidence
and documentation await the user's normal commit/push.

| Requirement | Evidence/status |
|---|---|
| Recall@5 >= 0.70 on 40 questions | Saved development retrieval result 1.000, synthetic/in-sample |
| API refusal >= 70% of ten negatives | 10/10 passed over public HTTPS |
| Tests locally and in CI, including tenant checks | 153 local tests passed; user reports green CI for 7c2f4fe |
| Clean-clone Compose runtime | Fresh committed clone passed build/up, initialization and authenticated tenant searches with isolated ports/volumes |
| Public cited answer | Passed before and after manual API restart |
| Pipeline explain-back | Deferred under the user's override, never marked passed |
| No swapping | Guest has no swap configured; snapshot measured, no peak/load claim |
| Results committed | Deployment/refusal evidence committed in 7c2f4fe; latest clean-clone evidence/report awaiting user's normal commit/push |

Docker Desktop is now running; full local tests and fresh Compose verification
completed. Temporary verification containers/volumes were removed without touching
the development or cloud stacks. Do not call the deferred learning check passed.

### Proxy configuration actually used

The user ran this in the Ubuntu SSH terminal after the API was ready and the
security-group rules were saved. Do not run it again against an existing container
of the same name. Named volumes preserve certificate state across recreation.

```bash
sudo docker run -d \
  --name support-copilot-proxy \
  --network host \
  --restart unless-stopped \
  --memory 256m \
  --log-opt max-size=5m \
  --log-opt max-file=2 \
  -v support-copilot-caddy-data:/data \
  -v support-copilot-caddy-config:/config \
  caddy:2.11.7 \
  caddy reverse-proxy \
  --from 16-178-30-70.sslip.io \
  --to 127.0.0.1:8001
```

Host networking makes the EC2 loopback API reachable from the proxy. Caddy's CLI
mode logs that its admin endpoint is disabled. HTTP port 80 redirects to HTTPS;
its HTTP/2/3 skip warnings do not indicate a failure of TLS on port 443.
Check the current instance IP before using this IP-encoded name after restart.
If it changes, recreate the proxy for the new hostname, retaining its data/config
volumes, then verify TLS and public behavior before sending tokens. Do not bypass
certificate verification. The API container can retain its original image/tag.

Public verification command (local Windows PowerShell, project directory):

```powershell
.venv\Scripts\python.exe scripts/smoke_knowledge.py --base-url https://16-178-30-70.sslip.io --output evals/results/day-05-public-https-smoke.json
```

No SSH forwarding is required for this URL. The script loads bearer tokens from
the ignored local .env without printing them. A closed SSH terminal does not stop
the detached containers. Stop the instance when leaving it unused to conserve
credits; EBS storage persists and may still consume credits. The free demo hostname
depends on third-party DNS availability and the current IP; it is not a stable
production domain or an availability guarantee. No rate-limiting guarantee is claimed.

The earlier preparation notes below are historical and superseded by this section.

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
