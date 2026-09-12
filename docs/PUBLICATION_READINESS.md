# Publication readiness: NutEV 1.1.0

Status: **PRODUCTION ACCEPTED / PUBLICATION PENDING**.

Production-acceptance baseline:

```text
e40dfd8c48cde824fa6053f9b077157f21bae698
```

The previous stable GitHub release `v1.0.0` and its Zenodo DOI remain unchanged.
This document does not claim a new tag, GitHub Release, archive deposit or DOI for
1.1.0.

## What is already accepted

The hosted 1.1.0 runtime has completed:

- required CI/security/browser gates on the same production target SHA;
- exact-SHA release prerequisite checks;
- trusted SSH host-key validation;
- host-level 80/443 inventory with preservation of the existing Caddy proxy;
- production recovery-readiness and disk-capacity validation;
- protected snapshot and bounded restore rehearsal;
- deployment and version/commit identity verification;
- public/runtime smoke;
- read-only post-deploy doctorate runtime audit.

The accepted hosted runtime uses `NUTEV_AUTH_MODE=pilot`.

## Distribution scope

The `nutev-nutmev` wheel and sdist distribute reusable Python modules and CLI.
They do not include hosted accounts, databases, private A1/A2 search state,
server backups or project-specific scientific ownership.

The website and hosted operational tools are deployed from an audited Git commit,
not from the wheel. Release notes must preserve this distinction.

## Scientific boundary

Software publication cannot approve scientific methodology.

A1 may remain `BLOCKED_SCIENTIFIC` pending genuine human/academic gates such as
PRESS/GF-10/freeze. A2 may remain `BLOCKED_PROVENANCE` or
`BLOCKED_SCIENTIFIC` pending reviewed historical provenance. Neither condition
blocks publication of the generic Engine when private surfaces stay isolated and
fail-closed.

No PRISMA state, screening decision, DOI, ownership binding or human approval may
be inferred from CI/deployment success.

## Hosted installation contract

Production uses provisioned access; there is no public self-service signup
promise. Runtime structure is scoped through user/workspace/project/application
boundaries.

Platform startup in `pilot` mode may initialize structural database schemas. It
must not fabricate users, workspaces, projects, ResearchApplications, A1/A2 state
or scientific decisions.

## Recovery contract

Production recovery now includes:

- full protected snapshot before promotion;
- byte/directory/mode/uid/gid inventory;
- SQLite/WAL integrity checks;
- bounded restore rehearsal to avoid a second full-volume copy;
- three complete rollback snapshots retained;
- current release explicitly protected;
- safe cleanup of incomplete recoveries only under reviewed allowlists;
- safe cleanup of unused images/cache without treating scientific volumes as
  disposable;
- a pre-deploy capacity gate that blocks release before mutation when required
  snapshot space is unavailable.

## Publication SHA rule

The production-acceptance baseline is not automatically the future publication
SHA. Documentation closeout may create a later commit.

Before tagging 1.1.0, designate one exact final SHA and run the complete required
publication gates on that exact commit. Do not transfer PASS from an earlier SHA
by assumption.

## Required publication steps

1. merge documentation closeout through normal review/status checks;
2. identify the exact final `main` SHA intended for `v1.1.0`;
3. confirm all required workflows PASS on that SHA;
4. build final wheel/sdist from that SHA;
5. run package audit, isolated install and container/privacy/recovery gates;
6. retain final artifact names and SHA-256 hashes outside expiring CI storage;
7. verify `CITATION.cff`, `.zenodo.json`, README and release notes agree on
   software identity;
8. create immutable tag `v1.1.0` at the exact publication SHA;
9. create GitHub Release with the final release notes/artifacts;
10. verify the archive service ingests the tagged snapshot;
11. record a version-specific DOI only after it is actually issued;
12. update current citation metadata with the real release date/DOI without
    moving the published tag.

## Metadata policy

Until publication:

- `version: 1.1.0` is allowed;
- production-accepted status may be documented;
- release date for 1.1.0 remains absent;
- DOI for 1.1.0 remains absent;
- v1.0.0 DOI remains explicitly historical only.

After real archive issuance, citation metadata can be updated to include the new
version-specific identifier. The tag must remain immutable.

## Optional providers

Google Programmable Search, Brave and SerpAPI are optional credentialed providers.
If credentials are absent, the runtime reports `skipped_config`; publication must
not rewrite that condition as a zero-result search or as universal provider
coverage.

## Evidence custody

Release evidence should retain:

- publication SHA;
- workflow/run identifiers;
- final wheel/sdist filenames and SHA-256 hashes;
- exact deployment/runtime identity;
- recovery-readiness evidence;
- package/container audit results;
- final GitHub Release URL;
- final archive record/DOI after issuance.

Do not retain private SSH material, credentials or scientific private state in
public release evidence.

See `docs/FINAL_SYSTEM_ACCEPTANCE.md`, `docs/SYSTEM_CLOSEOUT_MASTER.md`,
`docs/RELEASE_NOTES_1_1_0.md` and `docs/RELEASE_CHECKLIST.md`.
