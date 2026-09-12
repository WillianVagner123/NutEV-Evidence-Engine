# Final system acceptance — NutEV 1.1.0

**Decision: SOFTWARE PRODUCTION ACCEPTED / PUBLICATION PENDING.**

Production-acceptance baseline:

```text
e40dfd8c48cde824fa6053f9b077157f21bae698
```

The hosted NutEV 1.1.0 software completed the required exact-SHA release gates,
recovery-readiness checks, deployment and post-deploy runtime audit on the
baseline above. This decision accepts the hosted software/runtime; it does not
promote scientific validity, A1 methodology, A2 provenance or a new public
release/DOI.

## Accepted production evidence

The production baseline completed:

- all required main-branch CI/security/browser/release workflows on the same SHA;
- exact-SHA release prerequisite validation;
- trusted SSH host identity and host-level 80/443 ownership inventory;
- preservation of the existing external Caddy reverse proxy;
- recovery-readiness and storage-capacity gate before deployment;
- protected production snapshot;
- bounded restore rehearsal with byte/metadata and SQLite/WAL checks;
- production deployment of package version `1.1.0` in auth mode `pilot`;
- local/public runtime smoke and commit/version identity verification;
- read-only post-deploy doctorate runtime audit.

The final post-deploy audit explicitly verified:

```text
read_only = true
scientific_state_modified = false
legacy_binding_performed = false
search_executed = false
```

At acceptance time the audit reported zero materialized A1 ResearchApplications
and zero materialized A2 ResearchApplications. This is an intentional fail-closed
scientific state, not a software acceptance failure.

## Recovery acceptance

Recovery policy is now operationally bounded and fail-closed:

- three complete rollback snapshots are retained;
- the currently served release is explicitly protected;
- incomplete recoveries are removable only under reviewed allowlisted rules;
- images associated with failed deploys may be removed only when not referenced
  by containers and when the failed SHA is allowlisted;
- unused Docker builder cache may be reclaimed by the production recovery gate;
- scientific volumes are never treated as disposable cache;
- deployment does not proceed when required snapshot capacity is unavailable.

The final recovery-readiness cycle restored sufficient free capacity while
preserving three complete snapshots and without modifying scientific data.

## Product acceptance boundary

Accepted:

- hosted web runtime and provisioned multi-user `pilot` mode;
- tenant/project/application isolation contracts;
- authenticated browser lifecycle and onboarding behavior;
- exact-SHA deploy/recovery controls;
- package/container privacy boundaries;
- read-only post-deploy operational audit;
- standalone Python/CLI package identity at version 1.1.0.

Not implied by this acceptance:

- scientific superiority over alternative retrieval tools;
- systematic-review completeness;
- PRISMA completion;
- PRESS or GF-10 approval;
- human screening/adjudication;
- methodological quality, risk of bias or certainty assessment;
- A2 legacy ownership/provenance approval;
- access to licensed sources not actually configured;
- public publication of `v1.1.0`.

## A1 and A2

A1 and A2 remain private scientific workloads using the generic Engine.

A1 remains blocked by genuine scientific/human methodology gates. No CI or
production PASS can substitute for academic reviewer approval, PRESS, GF-10,
freeze or other required records.

A2 remains fail-closed until real provenance is sufficient to create reviewed
`LegacyBindingEvidence`. No ownership is inferred from historical names such as
`busca2a`/`busca2b`.

## Publication identity

Version 1.1.0 is **production accepted but unpublished**.

The historical `v1.0.0` tag and DOI remain unchanged. No DOI is assigned to
1.1.0 until an archive service actually issues a version-specific identifier.
The final publication SHA may be newer than the production-acceptance baseline if
this documentation closeout is merged; publication gates must therefore rerun on
the exact final SHA before an immutable `v1.1.0` tag is created.

See also:

- `docs/SYSTEM_CLOSEOUT_MASTER.md`;
- `docs/PUBLICATION_READINESS.md`;
- `docs/RELEASE_NOTES_1_1_0.md`;
- `docs/RELEASE_CHECKLIST.md`.
