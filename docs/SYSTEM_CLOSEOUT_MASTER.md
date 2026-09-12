# NutEV System Closeout Master

Audit closeout date: 2026-09-12, America/Sao_Paulo.

Production-acceptance baseline:

```text
e40dfd8c48cde824fa6053f9b077157f21bae698
```

Candidate/publication version: **1.1.0**.

Overall software state:

```text
PRODUCTION ACCEPTED
PUBLICATION PENDING
```

This master separates three identities that must not be conflated:

1. the production-acceptance SHA above;
2. any later documentation-only SHA created during release closeout;
3. the future immutable `v1.1.0` publication SHA.

A later documentation commit does not invalidate the historical production
acceptance evidence, but an immutable release tag must receive its own exact-SHA
publication gates.

## Immutable boundaries

Never fabricate counts, provider results, identifiers, human reviews, PRESS/GF-10
approval, A2 `LegacyBindingEvidence` or PRISMA state. Do not reassign historical
scientific ownership by inference. Global bibliographic identity is distinct from
private search/project/review state. UNKNOWN remains unbound.

Published tags, including `v1.0.0`, remain immutable. The historical DOI
`10.5281/zenodo.21998607` belongs to `v1.0.0` and must not be reused as the
version-specific DOI of 1.1.0.

PASS always names a SHA, environment and scope. CI, deploy, package artifacts and
scientific approval are separate gates.

## Production closeout evidence

The hosted 1.1.0 production baseline completed the following sequence:

```text
required CI/security/browser workflows
  -> exact-SHA release barrier
  -> recovery readiness
  -> trusted SSH and host-key pin
  -> 80/443 ownership inventory
  -> protected snapshot
  -> bounded restore rehearsal
  -> production promotion
  -> version/public smoke
  -> read-only doctorate runtime audit
```

The existing host-level Caddy proxy remained the owner of 80/443 and was not
replaced by a project container proxy.

The release pipeline also gained capacity hygiene so that deployment is blocked
before mutation when there is insufficient space for a protected snapshot.
Recovery retention preserves three complete snapshots, protects the currently
served release and can reclaim only explicitly disposable artifacts such as
unused Docker builder cache.

## Runtime acceptance

The production baseline was accepted with:

- semantic package version `1.1.0`;
- deployed commit identity matching the release target;
- `NUTEV_AUTH_MODE=pilot`;
- public web smoke passing;
- private scientific surfaces fail-closed without authentication;
- platform schema initialized without inventing users/projects/applications;
- post-deploy doctorate audit executed successfully and read-only.

The post-deploy audit verified:

```text
read_only = true
scientific_state_modified = false
legacy_binding_performed = false
search_executed = false
```

At acceptance time it found zero materialized A1 and zero materialized A2
ResearchApplications. That preserves scientific fail-closed semantics.

## Requirement ledger

| Requirement | Final state | Boundary |
|---|---|---|
| Core tests, identity, HTTP isolation and scientific guardrails | PASS on production baseline | Technical only |
| Authentication, stale-tab/logout and browser lifecycle | PASS | Does not prove all UX is optimal |
| Shared identity and private project/review separation | PASS | Scoped to tested contracts |
| Exact-SHA release prerequisites | PASS | Must rerun for future publication SHA |
| Python package boundary | PASS | Wheel/sdist exclude private runtime state |
| Docker private-data boundary | PASS | No claim of universal PII detection |
| Snapshot metadata/SQLite/WAL | PASS | ACL/xattr not broadly certified |
| Recovery rehearsal | PASS | Production-safe bounded rehearsal |
| Recovery capacity/retention | PASS | Three complete snapshots retained |
| Existing external Caddy preservation | PASS | Host-level proxy remains external |
| Production deployment | PASS | Baseline SHA above |
| Public/runtime acceptance | PASS | Hosted 1.1.0 runtime |
| Post-deploy doctorate audit | PASS | Read-only; 0 A1/0 A2 materialized |
| A1 scientific gates | BLOCKED_SCIENTIFIC | Genuine human/PRESS/GF-10/freeze evidence required |
| A2 legacy binding | BLOCKED_PROVENANCE / BLOCKED_SCIENTIFIC | Reviewed real provenance required |
| GitHub `v1.1.0` release | PENDING | Must point to final publication SHA |
| Zenodo/archive record for 1.1.0 | PENDING | DOI only after actual issuance |

## User/product closeout

The first-use hosted experience now distinguishes missing provisioned context from
an empty or broken application. A user without workspace/project receives explicit
guidance instead of a silent blank state. Chromium release coverage includes the
provisioned onboarding path through project context, search, Library and export.

A generation guard also prevents stale search executions from overwriting newer
results in the browser event lifecycle.

These fixes improve usability, but they do not substitute for ongoing product
research with real users.

## Scientific separation

A1 and A2 are private consumers of the generic platform, not hidden defaults of
the Engine.

A1 remains subject to its academic methodology contracts. A2 remains dark/fail-
closed until provenance is sufficient for reviewed binding. The software release
may be accepted/published while either scientific workload remains blocked.

## Publication closeout

The remaining software-release work is publication, not go-live:

1. merge this documentation closeout through normal PR gates;
2. designate the exact final publication SHA;
3. rerun exact-SHA release/build/artifact checks on that SHA;
4. retain final wheel/sdist hashes;
5. create immutable tag `v1.1.0` on that SHA;
6. create GitHub Release using `docs/RELEASE_NOTES_1_1_0.md`;
7. allow the archive service to ingest the release;
8. record the real version-specific DOI only after issuance;
9. update citation metadata without moving the published tag.

Use `docs/FINAL_SYSTEM_ACCEPTANCE.md`, `docs/PUBLICATION_READINESS.md`,
`docs/RELEASE_NOTES_1_1_0.md` and `docs/RELEASE_CHECKLIST.md` together for the
publication stage.
