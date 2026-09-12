# Final system acceptance — NutEV 1.1.0

**Decision: SOFTWARE PRODUCTION ACCEPTED / GITHUB RELEASED / ZENODO PENDING.**

Immutable release SHA:

```text
49588233ad2828b8fcc6140398ab55aedf7c03ef
```

Immutable tag:

```text
v1.1.0
```

GitHub publication date: **2026-09-12**.

The hosted NutEV 1.1.0 software completed the required exact-SHA gates, recovery
checks, production deployment and post-deploy read-only audit. The same exact
commit was then tagged and published as the stable GitHub Release `v1.1.0`.

This decision accepts and publishes the software. It does **not** promote
scientific validity, A1 methodology, A2 provenance or a Zenodo DOI that has not
actually been issued.

## Accepted production and release evidence

The final release SHA completed:

- 7/7 required CI/security/browser/release workflows on the same SHA;
- exact-SHA release prerequisite validation;
- trusted SSH host identity and host-level 80/443 inventory;
- preservation of the existing external Caddy reverse proxy;
- recovery-readiness and storage-capacity gates;
- protected production snapshot and bounded restore rehearsal;
- production deployment of package version `1.1.0` in auth mode `pilot`;
- local/public runtime smoke and commit/version identity verification;
- read-only post-deploy doctorate runtime audit;
- immutable Git tag `v1.1.0` at the exact deployed SHA;
- public GitHub Release with audited wheel/sdist and release evidence.

The first deployment attempt ended with a transient SSH `Broken pipe`; it did not
satisfy the release gate and therefore could not publish. An idempotent rerun of
the same exact-SHA deploy completed successfully without code changes or relaxed
gates.

## Post-deploy scientific boundary

The final auditor explicitly verified:

```text
read_only = true
scientific_state_modified = false
legacy_binding_performed = false
search_executed = false
A1 ResearchApplications = 0
A2 ResearchApplications = 0
```

This is an intentional fail-closed scientific state, not a software acceptance
failure.

## Recovery acceptance

Recovery policy is operationally bounded and fail-closed:

- three complete rollback snapshots are retained;
- the served release is protected;
- incomplete recoveries are removable only under reviewed rules;
- scientific volumes are never treated as disposable cache;
- unused Docker builder cache may be reclaimed when safe;
- deployment stops before mutation when required snapshot capacity is absent;
- restore rehearsal validates bytes, filesystem metadata and SQLite/WAL state.

## Product acceptance boundary

Accepted and released:

- hosted web runtime and provisioned multi-user `pilot` mode;
- tenant/project/application isolation contracts;
- authenticated browser lifecycle and onboarding behavior;
- exact-SHA deploy/recovery controls;
- package/container privacy boundaries;
- standalone Python/CLI package version 1.1.0;
- stable GitHub `v1.1.0` source/package release.

Not implied:

- scientific superiority over alternative retrieval tools;
- systematic-review completeness;
- PRISMA completion;
- PRESS or GF-10 approval;
- human screening/adjudication;
- methodological quality, risk of bias or certainty assessment;
- A2 legacy ownership/provenance approval;
- access to licensed sources not actually configured;
- a Zenodo DOI for 1.1.0 before a public archive record exists.

## A1 and A2

A1 and A2 remain private scientific workloads using the generic Engine.

A1 remains blocked by genuine scientific/human methodology gates where required.
No CI or production PASS substitutes for academic reviewer approval, PRESS,
GF-10, freeze, screening or adjudication.

A2 remains fail-closed until real provenance is sufficient to create reviewed
`LegacyBindingEvidence`. Ownership is not inferred from historical labels.

The general scientific validation state remains:

```text
B — DEMOTE
```

## Publication identity

Version 1.1.0 is **published on GitHub**.

Release identity:

```text
version = 1.1.0
tag = v1.1.0
sha = 49588233ad2828b8fcc6140398ab55aedf7c03ef
GitHub Release = https://github.com/WillianVagner123/NutEV-Evidence-Engine/releases/tag/v1.1.0
```

The historical `v1.0.0` DOI remains unchanged:

```text
10.5281/zenodo.21998607
```

No version-specific DOI is assigned to `v1.1.0` in this document because no
public Zenodo `v1.1.0` record has been verified. The published Git tag must remain
immutable even when current documentation later records a real archive DOI.

See also:

- `docs/SYSTEM_CLOSEOUT_MASTER.md`;
- `docs/PUBLICATION_READINESS.md`;
- `docs/RELEASE_NOTES_1_1_0.md`;
- `docs/RELEASE_CHECKLIST.md`.
