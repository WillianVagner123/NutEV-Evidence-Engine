# NutEV — Final Multi-tenant Release Gate

Status: **current production-promotion contract**.

## Purpose

Production promotion is fail-closed and exact-SHA. Software correctness, deployment success and scientific validity are separate gates.

For a candidate `main` SHA, release prerequisites must be green for that same source identity. A successful historical run, PR checkout or different SHA cannot satisfy the current promotion.

## Exact-SHA prerequisites

The maintained gate verifies the required CI/security/product workflows for the candidate commit, including:

```text
ci
security-scan
dependency-review
multitenant-release-audit
release-artifact-validation
codeql
predeploy-browser-e2e
```

The combined coverage includes Python 3.12/3.13 tests, Windows smoke, Ruff/typecheck, scientific guardrails, the full multi-tenant death test, distribution/container audits and authenticated Chromium product checks.

A required run that is missing, failed, skipped or belongs to another SHA does not satisfy promotion.

## Production runtime contract

Hosted multi-tenant production requires:

```text
NUTEV_AUTH_MODE=pilot
```

`legacy` remains a compatibility/recovery mode in code but is not the accepted hosted production baseline.

The runtime must expose the canonical provider registry and preserve private-surface fail-closed behavior without a valid platform session/guest credential. Legacy unscoped Workbench access is not treated as tenant-safe project access in pilot mode; project-safe Library/application/review surfaces remain authorization-scoped.

Article 1 and Article 2 private adapters remain subject to their own owner/provenance/scientific gates. Route availability or deployment does not approve PRESS/GF-10, create PRISMA state or activate historical binding.

## Deployment and recovery

The Hetzner promotion stage must:

1. revalidate release prerequisites for the exact target SHA;
2. use pinned SSH host identity/strict checking and step-scoped secrets;
3. preserve enough previous deployment/configuration identity for recovery;
4. create/verify the required read-only persistent-volume snapshot or equivalent recovery artifact;
5. prove isolated SQLite/WAL restore readiness before replacing the active image;
6. deploy the verified target commit;
7. verify the running application and edge behavior;
8. prove `/api/version`/runtime source identity equals the intended deployed SHA when that endpoint is available through the tested path.

A failed prerequisite, recovery check, SSH stage, runtime smoke or edge verification leaves promotion failed. The workflow must not weaken a scientific or security gate to make deployment green.

## Public edge and application boundary

Caddy/host controls provide transport/routing and may provide an outer compatibility perimeter. They do not replace application authentication or tenant authorization.

The release gate tests the application runtime directly enough that an outer Basic Auth response cannot hide an unsafe private-surface configuration.

## Post-deploy audit

After a successful production promotion, the maintained read-only doctorate/runtime audit may observe materialized A1/A2 application/workflow state. It is explicitly non-mutating and does not execute a search, create a legacy binding or manufacture scientific approval.

For first-party doctorate workloads, absence of reviewed owner/provenance evidence remains fail-closed even when the platform itself is healthy.

## Release identity versus moving `main`

The immutable software release and the moving production branch are distinct identities:

```text
v1.1.0 tag -> 49588233ad2828b8fcc6140398ab55aedf7c03ef
main       -> may advance through validated post-release fixes/docs/operations
```

Advancing `main` does not move or rewrite the `v1.1.0` tag/GitHub Release/Zenodo archive. Any post-release `main` deployment must independently pass the exact-SHA promotion contract.

## Scientific non-effects

A green production release/deploy does **not** by itself:

```text
validate a research question or search strategy
approve PRESS / GF-10 / query freeze
include or exclude evidence
adjudicate Human Review
activate Article 2 historical binding
create scientific PRISMA events
establish certainty, causality or recommendation validity
```

Those remain explicit scientific/human governance decisions.

## Completion rule

Operational production closeout for a candidate SHA requires:

```text
RELEASE_PREREQUISITES = PASS on exact SHA
RECOVERY_READINESS     = PASS
PRODUCTION_DEPLOY      = PASS
RUNTIME_EDGE_VERIFY    = PASS
POSTDEPLOY_AUDIT       = PASS when configured for the workload
```

Only then should that moving `main` SHA be described as the active validated production source. This contract does not redefine the immutable v1.1.0 release snapshot.
