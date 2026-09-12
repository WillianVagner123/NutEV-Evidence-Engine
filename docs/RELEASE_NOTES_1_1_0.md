# NutEV Reference Engine 1.1.0 — release notes candidate

Status: **production accepted / publication pending**.

Production-acceptance baseline:

```text
e40dfd8c48cde824fa6053f9b077157f21bae698
```

This document records the software state that completed hosted acceptance. It is
not a GitHub Release and does not claim a new DOI. The historical v1.0.0 release
and DOI remain immutable.

## Highlights

Version 1.1.0 turns the Reference Engine into a hosted, authenticated,
multi-tenant research platform while preserving the standalone Python/CLI
reference-discovery contracts.

Major additions include:

- provisioned `pilot` authentication for hosted production;
- workspace, project and ResearchApplication scoping;
- fail-closed private A1/A2 surfaces;
- exact-SHA release barriers and production deployment identity checks;
- authenticated Chromium coverage for onboarding, workspace/project switching,
  stale-tab/logout behavior and search/export lifecycle;
- multi-tenant death tests and source-ownership isolation;
- safe recovery snapshots with byte, directory, mode, uid/gid and SQLite/WAL
  validation;
- bounded restore rehearsal that avoids duplicating the full scientific volume;
- recovery-retention policy preserving three complete rollback snapshots and the
  currently served release;
- scoped Docker builder-cache hygiene to keep snapshot capacity above the
  required safety margin;
- preservation of the existing host-level Caddy reverse proxy instead of
  starting a competing container proxy;
- platform-schema bootstrap at startup in `pilot` mode without creating users,
  workspaces, projects, A1/A2 applications or scientific state;
- read-only post-deploy doctorate audit with preserved evidence artifacts;
- first-use UX guidance when a user has no workspace or no selected project;
- generation guards preventing stale search executions from overwriting newer
  UI results.

## Production acceptance

Hosted acceptance completed on the baseline SHA above with:

- exact-SHA prerequisites: PASS;
- deployment workflow: PASS;
- trusted SSH host identity: PASS;
- 80/443 ownership inventory: PASS;
- existing Caddy preserved;
- version `1.1.0` and deployed commit identity verified;
- production auth mode `pilot`;
- public web smoke PASS;
- private surfaces fail-closed without authentication;
- protected recovery snapshot and restore rehearsal PASS;
- recovery-capacity gate PASS while preserving three complete snapshots;
- post-deploy doctorate audit PASS and read-only.

The doctorate audit explicitly verified:

```text
read_only = true
scientific_state_modified = false
legacy_binding_performed = false
search_executed = false
```

At acceptance time, zero A1 and zero A2 ResearchApplications were materialized in
the hosted platform. That is an intentional fail-closed scientific state, not a
platform failure.

## Scientific boundary

Software acceptance does **not** promote scientific validity.

A1 remains dependent on genuine human academic review, PRESS/GF-10/freeze and
other protocol gates before formal-search/PRISMA claims are allowed. A2 remains
dependent on reviewed legacy provenance before any `LegacyBindingEvidence` may
be created. No scientific decision is inferred from CI, deployment or runtime
availability.

The broader scientific validation status of the Reference Engine also remains
separate from software release acceptance. Ranking tiers are information-
retrieval priorities, not methodological quality, eligibility, certainty or
clinical recommendations.

## Optional providers

Google Programmable Search, Brave and SerpAPI remain optional credentialed
providers. When credentials are absent, production records them as
`skipped_config`; absence is not reported as a fabricated zero-result search.

## Publication still pending

Before `v1.1.0` becomes a public release:

1. choose the final publication SHA after documentation closeout;
2. rerun the required exact-SHA gates on that final SHA;
3. build and retain the final wheel/sdist and their hashes;
4. create immutable tag `v1.1.0` on that exact SHA;
5. create the GitHub Release and attach the intended artifacts/evidence;
6. let the archive service ingest the real release;
7. record a version-specific DOI only after it is actually issued;
8. update citation metadata with the real release date/DOI without moving the
   published tag.

Until those steps occur, 1.1.0 is **production accepted but unpublished**.
