# NutEV — Final Multi-tenant Release Gate

Status: PR-13 deployment contract.

## 1. Purpose

PR-13 closes the release boundary. It does not change Article 1 or Article 2 scientific state. It makes the production promotion fail closed unless the running image proves the multi-tenant security contract.

A release is complete only when all of the following are true for the same `main` SHA:

```text
CI / pytest 3.12 + 3.13 PASS
Windows smoke PASS
Ruff + typecheck PASS
scientific guardrails PASS
Full Multi-tenant Death Test PASS
security-scan PASS
dependency-review PASS
release-artifact-validation PASS
CodeQL PASS
Chromium pre-deploy PASS
Hetzner deployment PASS
local production runtime smoke PASS
public HTTPS edge smoke PASS
/api/version == deployed SHA
```

## 2. Required production auth mode

Final multi-tenant production requires:

```text
NUTEV_AUTH_MODE=pilot
```

The release runtime smoke now rejects `legacy` mode.

This is deliberate. `legacy` remains a compatibility mode for older environments, but it is not accepted as the final multi-tenant release state.

## 3. Eleven-provider contract

The live runtime must expose exactly the canonical provider registry:

```text
pubmed
europepmc
openalex
crossref
doaj
semantic_scholar
google_pse
brave
serpapi
lilacs_bvs_native
scielo_native
```

The smoke verifies registry identity/order and UI labels. It does not query external providers and therefore does not create a scientific search event.

## 4. Private-surface unauthenticated contract

Without a platform session, the local application runtime must fail closed for:

```text
/api/auth/me                         -> 401
/api/context                         -> 401
/api/searches                        -> 401
/api/articles                        -> 401
/api/library                         -> 401
/agent-context/article1/SEARCH_STATE.json -> 401
/api/article1/d132/review             -> 401 without guest token
/api/article2/integrative/status      -> 401 when enabled, or 404 while dark-launched
```

### Legacy Workbench

The current Workbench projection contains mixed global bibliographic identity and scientific projection state. Therefore, in `pilot` mode:

```text
/api/articles*
```

is not exposed through the legacy API, even to an authenticated project user. The tenant-safe replacement is the Evidence Library (`/api/library`).

`legacy` mode behavior is preserved for backwards compatibility and is not accepted by the final release smoke.

### Article 1 static context

The persistent Article 1 agent context is private scientific material. In `pilot` mode the static path:

```text
/agent-context/article1/*
```

requires:

```text
authenticated Principal
+ selected workspace/project
+ current application template == SCOPING_REVIEW
+ assembly_id == WILLIAN_DOCTORATE_A1
```

A wrong project receives not-found semantics; knowing the static path is not authorization.

### Article 2

Article 2 remains a private `INTEGRATIVE_REVIEW` application. Its HTTP routes are dark-launched behind `NUTEV_ARTICLE2_ENABLED`. The release gate accepts 404 while dark-launched because historical ownership binding remains blocked. Enabling the route does not activate legacy binding; unauthenticated access must still return 401.

## 5. Public edge contract

Caddy remains an outer perimeter. Public HTTPS smoke accepts:

```text
200
or
401 Basic Auth
```

on protected edge surfaces.

If `/api/version` is publicly reachable with HTTP 200, its `commit` must equal the deployment `TARGET_SHA` exactly.

The deeper authentication/tenant checks are executed against the local running container before promotion and again against the production container, so Basic Auth cannot hide an unsafe application runtime behind the edge.

## 6. Current operational blocker (2026-09-08)

The latest automatic deploy for:

```text
main = 2717bbd42b8fa72da6af8b3d5eec1ae4a778f391
```

failed before any SSH connection was attempted.

Failure stage:

```text
Configure SSH
```

Failure contract:

```text
HETZNER_SSH_KEY could not be parsed as an unencrypted private SSH key
```

Therefore:

```text
production was NOT changed
SSH access was NOT attempted
container preflight was NOT executed
public smoke was NOT executed
```

The GitHub Environment secret must contain the complete **private** SSH key, unencrypted/no passphrase, whose public half is present in the target user's `authorized_keys`.

Do not place the private key in source control, issues, PR comments, logs or chat.

After SSH is corrected, a second configuration gate may still intentionally stop deployment if the server `.env` does not contain:

```text
NUTEV_AUTH_MODE=pilot
```

That is a required release condition, not a workaround to bypass.

## 7. No scientific mutation

PR-13 does not:

```text
execute a scientific search
query external providers
rerank evidence
change Registry article identity
rewrite Workbench
change Article 1 D-132 decisions
change PRESS / GF-10 / freeze
activate Article 2 legacy binding
create PRISMA events
adopt historical searches
apply the PR-7 migration planner
```

## 8. Release completion rule

Do not label the migration or production release complete merely because PR-13 code is merged.

Final state is:

```text
RELEASE_READY_CODE = all code/CI gates green
PRODUCTION_DEPLOYED = Hetzner deploy job green
PUBLIC_VERIFIED = deployed /api/version SHA + edge smoke green
```

Only when all three are true may the final multi-tenant rollout be called complete.

## Closeout hardening (2026-09-10)

PR #1246 adds an exact-SHA seven-workflow barrier and revalidation after environment approval, including the separately named authenticated pilot Chromium job. Missing/failed/skipped/foreign/old executions cannot satisfy promotion. The final main SHA must have its own trusted runs; PR checkouts are not deployed evidence.

SSH is the final operational stage per owner instruction. Both readiness and deployment require a separately verified HETZNER_KNOWN_HOSTS pin with strict host checking; private keys remain step-scoped. Before replacing the image, deployment preserves old configuration/image identity and requires a quiesced read-only volume snapshot with successful isolated SQLite/WAL restore proof. Recovery verifies the old version and does not overwrite scientific data. Synthetic tests do not establish actual server recovery.

A1 static and D-132 source access additionally require server-managed workspace/project owner pins based on reviewed runtime evidence. A writable application assembly label alone is insufficient. A2's dark-launch and provenance gate are unchanged. No SSH credential or actual production owner mapping was configured by these code changes.
