# Publication readiness: NutEV 1.1.0

Status: **GITHUB RELEASED / ZENODO ARCHIVE PENDING**.

Immutable publication SHA:

```text
49588233ad2828b8fcc6140398ab55aedf7c03ef
```

GitHub publication date: **2026-09-12**.

GitHub Release:

```text
https://github.com/WillianVagner123/NutEV-Evidence-Engine/releases/tag/v1.1.0
```

The historical `v1.0.0` DOI remains `10.5281/zenodo.21998607`. It must not be
reused for `v1.1.0`.

## Completed publication gates

The exact publication SHA completed:

- 7/7 required CI/security/browser/release workflows on the same SHA;
- build and validation of wheel/sdist;
- clean isolated wheel installation;
- public distribution audit;
- actual container/privacy/recovery audit;
- exact-SHA release prerequisites;
- production deployment on Hetzner;
- local/public runtime smoke and version identity checks;
- successful read-only post-deploy doctorate audit;
- immutable Git tag `v1.1.0` on the exact publication SHA;
- public GitHub Release with audited release assets and hashes.

The release includes:

```text
nutev_nutmev-1.1.0-py3-none-any.whl
nutev_nutmev-1.1.0.tar.gz
distributions.json
SHA256SUMS.txt
release-evidence.json
container-audit.zip
release-prerequisites.zip
```

## Post-deploy scientific boundary

The post-deploy auditor passed with:

```text
read_only = true
scientific_state_modified = false
legacy_binding_performed = false
search_executed = false
A1 ResearchApplications = 0
A2 ResearchApplications = 0
```

Software publication therefore does not manufacture or promote A1/A2 scientific
state. The general validation state remains `B — DEMOTE`.

## Distribution scope

The `nutev-nutmev` wheel and sdist distribute reusable Python modules and CLI.
They do not include hosted accounts, databases, private A1/A2 search state,
server backups or project-specific scientific ownership.

The website and hosted operational tools are deployed from the audited Git
commit, not from the wheel. Public package and hosted runtime are related but
have different content boundaries.

## Scientific boundary

A1 remains subject to genuine human/academic gates such as PRESS, GF-10, freeze,
screening and adjudication where required by its protocol.

A2 remains fail-closed until real historical provenance supports reviewed
`LegacyBindingEvidence`.

No CI, deploy, GitHub tag or software release can substitute for those scientific
records.

## Remaining external publication gate

The only unfinished archive step for the software release is a version-specific
Zenodo (or equivalent) archival record.

Current verified state:

```text
GitHub v1.1.0 = RELEASED
Zenodo v1.1.0 = NOT VERIFIED / PENDING
DOI v1.1.0 = ABSENT UNTIL REAL ISSUANCE
```

Public Zenodo search did not show a `NutEV Reference Engine 1.1.0` record after
the GitHub release. Do not infer a DOI from the historical v1.0.0 record or from
a concept identifier.

If Zenodo is connected to the GitHub repository, verify that it ingests the
`v1.1.0` release. If it is not connected, an authenticated Zenodo user must
create/publish the software deposit using the immutable tagged release and its
release metadata. Only after the public record exists should the new DOI and
archive publication date be written into current citation/archive metadata.

## Metadata policy after GitHub release

Current operational documentation may state:

- version `1.1.0`;
- GitHub publication date `2026-09-12`;
- immutable Git tag `v1.1.0`;
- immutable release SHA `49588233ad2828b8fcc6140398ab55aedf7c03ef`;
- GitHub Release URL.

Until the archive exists, citation/archive metadata intentionally keeps these
fields absent:

```text
CITATION.cff date-released
CITATION.cff DOI
.zenodo.json archive publication date
.zenodo.json DOI
```

This is enforced by the repository metadata contract. The GitHub release date and
an eventual Zenodo archive date are related publication events but are not
silently conflated.

## Evidence custody

Public release evidence retains:

- publication SHA;
- workflow/run identity;
- final wheel/sdist and SHA-256 hashes;
- package/container audit evidence;
- release-prerequisite evidence;
- sanitized post-deploy scientific boundary;
- GitHub Release identity.

Private SSH material, credentials and private scientific state are not part of
public release evidence.

See `docs/FINAL_SYSTEM_ACCEPTANCE.md`, `docs/SYSTEM_CLOSEOUT_MASTER.md`,
`docs/RELEASE_NOTES_1_1_0.md` and `docs/RELEASE_CHECKLIST.md`.
