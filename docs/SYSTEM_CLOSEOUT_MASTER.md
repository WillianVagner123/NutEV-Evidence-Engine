# NutEV System Closeout Master

Audit date: 2026-09-12, America/Sao_Paulo.

Production version: **1.1.0**.  
Production SHA: **`e40dfd8c48cde824fa6053f9b077157f21bae698`**.  
Operational verdict: **PASS — SITE / SOFTWARE CLOSED**.  
Publication verdict: **PENDING — GitHub Release / Zenodo not yet verified**.

## Immutable boundaries

No fabricated counts, provider results, identifiers, human reviews, PRESS/GF-10 approval, A2 LegacyBindingEvidence or PRISMA. No production data mutation or historical reassignment. No scoring/taxonomy/query expansion is implied by release documentation.

Published tags, including `v1.0.0`, remain unchanged. The future `v1.1.0` tag must point exactly to the homologated production SHA and must not be moved after publication.

PASS always names a SHA, command/environment scope and evidence boundary. Production acceptance does not imply scientific validation.

## Final operational evidence

The 1.1.0 production closeout recorded:

- 7/7 workflows green on the same release SHA;
- Hetzner recovery readiness PASS;
- snapshot capacity PASS;
- three complete rollback snapshots retained;
- active release protected;
- exact-SHA deployment `#1659` PASS;
- Caddy edge on ports 80/443 PASS;
- public `/search.html` and `/articles.html` returning HTTP 200;
- private unauthenticated surfaces returning HTTP 401 / fail-closed;
- real backup and restore PASS;
- 19.466 files verified;
- 33 SQLite databases verified;
- `production_overwritten=false`;
- post-deploy auditor `#99` PASS;
- final auditor executed rather than remaining skipped;
- auditor state: `read_only=true`, `scientific_state_modified=false`, `legacy_binding_performed=false`, `search_executed=false`;
- 0 A1 and 0 A2 applications materialized in production.

The capacity remediation is intentionally bounded: it reclaims only unused Docker build cache while preserving the active release, three complete rollback points, runtime images and the scientific volume.

## Requirement ledger

| Requirement | Final state | Evidence / boundary |
|---|---|---|
| Core tests / CI | PASS | 7/7 workflows on release SHA |
| Authentication / tenant isolation | PASS | production and browser/release gates |
| Private unauthenticated surfaces | PASS | 401 / fail-closed |
| Public site | PASS | `/search.html`, `/articles.html` = 200 |
| Exact-SHA deploy | PASS | deploy `#1659` |
| Hetzner readiness | PASS | real host/recovery checks |
| Backup / restore | PASS | real restore without production overwrite |
| Recovery retention | PASS | 3 complete snapshots preserved |
| File integrity | PASS | 19.466 files verified |
| SQLite integrity | PASS | 33 databases verified |
| Post-deploy audit | PASS | auditor `#99` |
| Scientific-state immutability | PASS | no modification detected |
| A1 materialization | BLOCKED / FAIL-CLOSED | no human academic approval inferred |
| A2 Legacy Binding | BLOCKED / FAIL-CLOSED | no provenance inferred |
| GitHub tag/release `v1.1.0` | PENDING | external publication operation not yet verified |
| Zenodo 1.1.0 record / DOI | PENDING | new archive record must be created and verified |
| Backlog PR triage | SEPARATE SPRINT | not a production blocker |

## Production verdict

```text
SITE / SOFTWARE NUTEV 1.1.0 — PRODUCTION: PASS — CLOSED
```

This verdict covers the deployed product and operational recovery posture only.

## Publication verdict

Until tag, GitHub Release and archive record exist and are externally verified:

```text
PRODUCTION_ACCEPTED / PUBLICATION_PENDING
```

After verified GitHub publication and verified archive/DOI:

```text
RELEASED / PUBLISHED
```

The DOI `10.5281/zenodo.21998607` remains associated with historical `v1.0.0` and must not be assigned to `v1.1.0`.

## Scientific boundary

A1 remains scientific, not technical. PR #1230 is intentionally open/draft while D-132 awaits academic approval and nominal human verifier designation. Formal search/PRESS, freeze, GF-10 and PRISMA remain downstream gates.

A2 remains fail-closed until real historical provenance and reviewed Legacy Binding evidence exist. Production correctly materializes neither A1 nor A2 by inference.

The Engine scientific-validation status remains governed by the files in `validation/`; software go-live does not promote that state.

## Maintenance / backlog

Historical search-expansion and Dependabot PRs are not release blockers. They must be handled in a separate maintenance sprint with explicit disposition:

```text
MERGE / SUPERSEDED / CLOSE / FUTURE
```

Do not mix that cleanup into the immutable 1.1.0 production acceptance record.

## Canonical references

- `README.md` — public project status;
- `docs/releases/v1.1.0-production-closeout.md` — operational closeout;
- `docs/FINAL_SYSTEM_ACCEPTANCE.md` — final software acceptance;
- `docs/PUBLICATION_READINESS.md` — remaining release/archive steps;
- `docs/ROLLBACK_RUNBOOK.md` — recovery contract;
- `docs/HETZNER_AUTODEPLOY.md` — production deployment contract;
- `docs/OPEN_PR_DISPOSITION.md` — backlog handling.
