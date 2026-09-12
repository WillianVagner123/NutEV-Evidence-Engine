# NutEV Reference Engine 1.1.0 — release notes

Status: **production accepted / GitHub released / Zenodo archived**.

Immutable GitHub release identity:

```text
version = 1.1.0
tag = v1.1.0
release_sha = 49588233ad2828b8fcc6140398ab55aedf7c03ef
published_at = 2026-09-12
zenodo_record = 22726717
doi = 10.5281/zenodo.22726717
```

Production acceptance originally closed on baseline SHA:

```text
e40dfd8c48cde824fa6053f9b077157f21bae698
```

Subsequent release-closeout work was validated again, and the final public GitHub
release was created from the immutable release SHA shown above. Later documentation
commits on `main` do not alter that published snapshot.

The historical `v1.0.0` Zenodo DOI remains immutable:

```text
10.5281/zenodo.21998607
```

That DOI is **not** the DOI of `v1.1.0` and is not reused. The verified
version-specific archive DOI for `v1.1.0` is:

```text
10.5281/zenodo.22726717
```

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

Hosted acceptance completed and was reconfirmed through the release-closeout
pipeline with:

- seven required release workflows on one candidate SHA: PASS;
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

Software acceptance and GitHub/Zenodo publication do **not** promote scientific
validity.

A1 remains dependent on genuine human academic review, PRESS/GF-10/freeze and
other protocol gates before formal-search/PRISMA claims are allowed. A2 remains
dependent on reviewed legacy provenance before any `LegacyBindingEvidence` may
be created. No scientific decision is inferred from CI, deployment, runtime
availability or archive publication.

The broader scientific validation status of the Reference Engine also remains
separate from software release acceptance. Ranking tiers are information-
retrieval priorities, not methodological quality, eligibility, certainty or
clinical recommendations.

## Optional providers

Google Programmable Search, Brave and SerpAPI remain optional credentialed
providers. When credentials are absent, production records them as
`skipped_config`; absence is not reported as a fabricated zero-result search.

## Public release state

The software publication is complete:

1. final publication SHA selected and validated;
2. required exact-SHA gates passed;
3. final wheel/sdist built and retained with hashes;
4. immutable tag `v1.1.0` created at
   `49588233ad2828b8fcc6140398ab55aedf7c03ef`;
5. GitHub Release published with audited artifacts/evidence;
6. post-release documentation reconciled without moving the tag;
7. production redeploy and read-only post-deploy audit passed again;
8. GitHub↔Zenodo integration enabled and synchronized;
9. Zenodo record `22726717` confirmed for software version `1.1.0`;
10. version-specific DOI `10.5281/zenodo.22726717` recorded.

## Zenodo archive state

Zenodo archive publication is complete for `v1.1.0`.

```text
record = 22726717
record URL = https://zenodo.org/records/22726717
DOI = 10.5281/zenodo.22726717
```

The archive closeout is a post-release metadata operation. It does not move,
delete, recreate or retag `v1.1.0`. The canonical operational tracking issue is
GitHub issue `#1262`, which may close only after the DOI metadata PR passes the
normal repository gates and merges successfully.
