# NutEV Hetzner auto-deploy

## Goal

Deploy the exact commit that passed the `ci` workflow on `main` to the existing Hetzner host without deleting the persistent NutEV data volume.

A successful `/api/health` response alone is not considered sufficient evidence for production promotion. The deploy also validates the runtime contract, persistent-volume write access, build identity and the public HTTPS edge.

## Trigger

`.github/workflows/deploy-hetzner.yml` supports two distinct paths.

### Automatic deploy

A completed `ci` workflow triggers production deploy only when:

- CI concluded with `success`;
- CI head branch is `main`;
- repository/environment variable `HETZNER_AUTODEPLOY` equals `true`.

### Manual deploy

`workflow_dispatch` can explicitly deploy the currently selected `main` commit even when `HETZNER_AUTODEPLOY` is disabled. Manual dispatch is restricted to `refs/heads/main`; it cannot be used to publish an arbitrary feature branch.

Leaving `HETZNER_AUTODEPLOY` unset or false disables only the automatic workflow-run path; it does not disable an explicit manual deploy from `main`.

## GitHub production environment

Create an environment named `HETZNER` to match the workflow and configure:

### Environment/repository variables

- `HETZNER_HOST`: server hostname or IP;
- `HETZNER_USER`: SSH deployment user;
- `HETZNER_APP_DIR`: absolute repository path on the server;
- `HETZNER_PORT`: optional SSH port; blank means 22;
- `HETZNER_AUTODEPLOY`: optional; set to `true` only when every successful `main` CI should deploy automatically;
- `NUTEV_PUBLIC_URL`: optional public base URL used by the edge smoke; blank defaults to `https://nutev.mindsperformance.com.br`;
- `HETZNER_COMPOSE_SERVICES`: optional space-separated Compose services the deploy starts; blank defaults to `nutev caddy`. Set it to `nutev` on hosts where the HTTPS edge is not the Compose `caddy` service (for example a host-level Caddy already bound to ports 80/443). Every name is validated against `docker compose config --services` before any container is replaced.

### Secret

- `HETZNER_SSH_KEY`: complete **private** SSH key dedicated to deployment. Use an unencrypted OpenSSH/PEM private key whose public half is installed in the target user's `~/.ssh/authorized_keys`. Do not store the `.pub` key in this secret.

The secret may be stored in any of these lossless representations:

- the raw multiline OpenSSH/PEM private-key block;
- a one-line value containing literal `\n` sequences;
- base64 of the complete private-key block.

The workflow normalizes Windows CRLF, literal `\n` sequences and valid base64-wrapped private keys before use. It never logs key material. It explicitly rejects public-key forms such as `ssh-ed25519 AAAA...`, `ssh-rsa AAAA...` and `-----BEGIN PUBLIC KEY-----`, validates the normalized private key with `ssh-keygen`, and performs a non-interactive SSH probe before any Git/Docker operation on the server.

Invalid, truncated or passphrase-protected private keys fail before deployment.

## Current SSH recovery

If the workflow reports:

```text
HETZNER_SSH_KEY could not be parsed as an unencrypted private SSH key
```

or an older SSH/OpenSSL path reports `Load key ... error in libcrypto`, treat both as a key-material/configuration failure. No container or production data has been changed yet at that stage. Correct the GitHub Environment `HETZNER` secret before rerunning the deploy.

The secret must look like a complete private key envelope, for example:

```text
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

Never paste a public key (`ssh-ed25519 AAAA...`, `ssh-rsa AAAA...` or a `.pub` file) into `HETZNER_SSH_KEY`. The public half belongs only in the target user's `~/.ssh/authorized_keys`.

Do not paste the real private key into issues, pull requests, logs, documentation or chat.

## Server prerequisites

The deployment user must be able to:

- authenticate with the public half of `HETZNER_SSH_KEY`;
- read/write the repository at `HETZNER_APP_DIR`;
- fetch `origin/main`;
- run Docker and Docker Compose;
- read `deploy/hetzner/.env`.

The production `.env` remains on the server and is never committed.

## Offline runtime contract

`tools/check_predeploy_runtime_contract.py` is deliberately network-free. It must not query PubMed or any other external scientific source. Its purpose is operational readiness, not evidence retrieval.

It validates:

- exactly 11 canonical public providers and their UI labels;
- critical public files (`index.html`, `search.html`, `articles.html`, `advanced.html`, `product-ui.js`, `app.js`);
- valid `config/reference_mode.json`;
- Quick search query compilation for all 11 providers;
- structured PICO query compilation for all 11 providers;
- literal/versioned Exact PubMed query compilation;
- image build identity when `build-info.json` is materialized;
- optional provider credentials as explicit `skipped_config` warnings rather than false evidence absence;
- optional persistent-output write probe that creates, fsyncs and removes a temporary file.

Contract states:

- `READY`: no failure or warning;
- `READY_WITH_WARNINGS`: operationally promotable, with explicit non-fatal warnings such as optional web-provider credentials not configured;
- `NOT_READY`: fail closed; deployment must stop/rollback.

The contract does not change Registry identity, ranking, CORE, MEV, PRESS/PRISMA, eligibility or scientific inclusion state.

## Readiness check before deploy

`.github/workflows/hetzner-readiness.yml` is a manual, `main`-only preflight that uses the same `HETZNER` environment but does **not** deploy or replace containers.

It verifies:

- deployment variables and SSH secret are present;
- the SSH key can be normalized and parsed as an unencrypted private key;
- SSH authentication succeeds;
- `HETZNER_APP_DIR` is a Git repository;
- `deploy/hetzner/.env`, `compose.yaml`, and `Dockerfile` exist;
- Git, Docker, Docker Compose, and curl are available;
- Docker daemon access works;
- current repository SHA, branch, Docker version, and free disk space can be read;
- current local health/version endpoints are reported when available.

The readiness workflow intentionally does **not** run `git reset`, build images, start/stop containers, prune images, migrate Registry data or mutate volumes.

## Release runbook

1. Generate or recover a dedicated unencrypted deployment private key and install its **public** half in the deployment user's `~/.ssh/authorized_keys`.
2. Store the complete **private** half in GitHub Environment `HETZNER` as `HETZNER_SSH_KEY`.
3. Run **hetzner-readiness** on `main`.
4. Stop if SSH configuration/access or remote prerequisites fail.
5. Run **deploy-hetzner** manually from `main`, or allow automatic deployment only when `HETZNER_AUTODEPLOY=true`.
6. Confirm the exact `TARGET_SHA` is used.
7. Confirm isolated preflight health + runtime contract + preflight build identity.
8. Confirm production health + persistent-volume write probe + production build identity.
9. Confirm public HTTPS edge smoke.
10. Only then perform the authenticated user journey smoke: home -> search -> results -> Library -> article dossier.

## Deployment sequence

```text
manual main dispatch OR successful main CI with autodeploy enabled
  -> resolve exact TARGET_SHA
  -> normalize and validate private SSH key
  -> reject public/private-key format mistakes
  -> non-interactive SSH probe
  -> SSH to Hetzner
  -> fetch origin/main and reset to TARGET_SHA
  -> build nutev:<sha> with immutable build identity
  -> isolated preflight container on 127.0.0.1:18765
  -> preflight /api/health
  -> offline runtime contract in preflight
  -> preflight /api/version == TARGET_SHA
  -> tag previous production image as nutev:rollback
  -> switch configured production services to nutev:<sha>
  -> production /api/health on 127.0.0.1:8765
  -> offline runtime contract in production + write probe on persistent volume
  -> production /api/version == TARGET_SHA
  -> public HTTPS edge smoke
  -> success
```

## Public HTTPS edge and Basic Auth

The Caddy configuration protects the domain with Basic Auth. Therefore an unauthenticated edge probe has two acceptable states only:

- HTTP `200`: the route is intentionally accessible without Basic Auth;
- HTTP `401`: the protected edge is reachable and correctly challenging for authentication.

The deployment workflow probes:

- `/api/health`;
- `/api/version`;
- `/search.html`;
- `/articles.html`.

If `/api/version` is accessible with HTTP `200`, its commit must equal `TARGET_SHA`. If Caddy returns `401`, the workflow does not bypass authentication; build identity has already been verified through the local backend before the edge check.

Other HTTP statuses, connection failure or TLS failure fail the edge smoke and trigger rollback when a previous image exists.

## Rollback

Before promotion, the previous running image is tagged `nutev:rollback` when a prior container exists.

Any post-promotion failure in production health, runtime contract, persistent write probe, local build identity or public edge smoke attempts to restore `nutev:rollback` and exits the workflow as failed.

On a first-ever deployment where no previous image exists, there is nothing to restore; the workflow still fails closed.

## Persistence

`deploy/hetzner/compose.yaml` uses the named volume:

```text
nutev_output:/app/project_output_reference
```

Normal deploys use `docker compose up`, not `down -v`, so searches, Registry, CORE outputs, Workbench SQLite, Radar/Watch and other persisted data survive container recreation.

The runtime write probe is intentionally temporary: it creates one small file, fsyncs it and removes it. It does not migrate or rewrite historical scientific data.

## Network boundary

NutEV port 8765 binds only to host loopback:

```text
127.0.0.1:8765:8765
```

Caddy is the public 80/443 entrypoint and applies TLS plus Basic Auth. Do not expose 8765 in the Hetzner firewall.

## First activation

Before enabling automatic deployment, verify once on the server:

```bash
cd /absolute/path/to/NutEV-Evidence-Engine
cp deploy/hetzner/.env.example deploy/hetzner/.env  # only if .env does not already exist
# fill real domain/auth/provider values in deploy/hetzner/.env
docker compose --env-file deploy/hetzner/.env -f deploy/hetzner/compose.yaml config
docker compose --env-file deploy/hetzner/.env -f deploy/hetzner/compose.yaml up -d --build
curl -fsS http://127.0.0.1:8765/api/health
python tools/check_predeploy_runtime_contract.py --output-root project_output_reference --write-probe --json
```

If the live server already has a valid `.env`, keep it. Do not overwrite it during activation.

After this preflight, either keep `HETZNER_AUTODEPLOY` disabled and release with `workflow_dispatch` from `main`, or set it to `true` to enable automatic deployment after successful `main` CI.
