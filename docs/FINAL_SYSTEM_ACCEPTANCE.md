# Final system acceptance — NutEV 1.1.0

**Decision: PRODUCTION PASS / SITE-SOFTWARE CLOSED.**

Production SHA:

```text
e40dfd8c48cde824fa6053f9b077157f21bae698
```

The NutEV 1.1.0 site/software acceptance is complete for the deployed production system. This document supersedes the prior candidate-state wording that still described real-server deployment and production acceptance as pending.

## Accepted production scope

The accepted system includes:

- authenticated multi-tenant project isolation;
- stale browser/tab/logout protection;
- scoped library/review/export services;
- first-party source-owner checks;
- fail-closed private surfaces;
- exact-SHA release controls;
- explicit Python and Docker package boundaries;
- snapshot integrity and recovery controls;
- public HTTPS edge behind Caddy;
- deployed NutEV 1.1.0 runtime on the Hetzner production host.

## Final evidence

Final closeout recorded:

- 7/7 workflows passing on the same release SHA;
- Hetzner recovery readiness PASS;
- snapshot-capacity gate PASS;
- three complete rollback snapshots preserved;
- active release protected;
- exact-SHA deploy `#1659` PASS;
- NutEV 1.1.0 active in production;
- external Caddy / ports 80–443 PASS;
- `/search.html` and `/articles.html` returning 200;
- private unauthenticated surfaces returning 401 / fail-closed;
- real backup/restore PASS;
- 19.466 files verified;
- 33 SQLite databases verified;
- `production_overwritten=false`;
- post-deploy auditor `#99` PASS;
- final auditor state `read_only=true`;
- `scientific_state_modified=false`;
- `legacy_binding_performed=false`;
- `search_executed=false`;
- 0 A1 / 0 A2 applications materialized.

The production capacity fix is bounded to unused Docker builder cache and preserves the active release, three full rollback snapshots, runtime images and the scientific volume.

## Acceptance verdict

```text
SITE / SOFTWARE NUTEV 1.1.0 — PRODUÇÃO: PASS — FECHADO E CONCLUÍDO
```

## What this acceptance does not claim

This is not a scientific-validation certificate and does not approve or materialize A1/A2.

A1 still requires genuine academic/human gates. A2 still requires reviewed provenance / Legacy Binding evidence. The production auditor finding zero materialized A1/A2 applications is the correct fail-closed behavior.

The NutEV Engine's validation status remains controlled by `validation/` and is not promoted by operational success.

## Publication identity

Production acceptance and public publication are separate states.

At the time of this document:

```text
PRODUCTION_ACCEPTED / PUBLICATION_PENDING
```

The next public-release operation must create an immutable `v1.1.0` tag pointing exactly to the accepted SHA above, followed by a GitHub Release and a new archive deposit. The historical DOI `10.5281/zenodo.21998607` belongs to `v1.0.0` and must not be reused.

Only after the tag, GitHub Release and new archive/DOI are verified may the software publication state become:

```text
RELEASED / PUBLISHED
```

See `docs/releases/v1.1.0-production-closeout.md`, `docs/SYSTEM_CLOSEOUT_MASTER.md` and `docs/PUBLICATION_READINESS.md`.
