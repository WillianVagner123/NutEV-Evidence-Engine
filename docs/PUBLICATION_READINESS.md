# Publication readiness: NutEV 1.1.0

Status: **GITHUB RELEASED / ZENODO ARCHIVED / DOI VERIFIED**.

Immutable publication SHA:

```text
49588233ad2828b8fcc6140398ab55aedf7c03ef
```

GitHub publication date: **2026-09-12**.

GitHub Release:

```text
https://github.com/WillianVagner123/NutEV-Evidence-Engine/releases/tag/v1.1.0
```

Zenodo archive:

```text
record = 22726717
DOI = 10.5281/zenodo.22726717
record URL = https://zenodo.org/records/22726717
```

The historical `v1.0.0` DOI remains `10.5281/zenodo.21998607`. It is not reused
for `v1.1.0`.

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
- public GitHub Release with audited release assets and hashes;
- GitHub↔Zenodo repository integration enabled and synchronized;
- public Zenodo archive identity confirmed for software version `1.1.0`;
- version-specific Zenodo DOI `10.5281/zenodo.22726717` recorded.

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

No CI, deploy, GitHub tag, GitHub Release or Zenodo archive can substitute for
those scientific records.

## Archive publication complete

The public software archive gate for `v1.1.0` is complete.

Verified state:

```text
GitHub v1.1.0 = RELEASED
Zenodo v1.1.0 = ARCHIVED
Zenodo record = 22726717
DOI v1.1.0 = 10.5281/zenodo.22726717
```

Authenticated evidence from the repository owner confirmed that
`WillianVagner123/NutEV-Evidence-Engine` is enabled in the GitHub↔Zenodo
integration, the repository synchronized successfully, the Zenodo DOI badge is
`10.5281/zenodo.22726717`, and the corresponding record is software version
`1.1.0`.

The archive closeout is metadata-only. It does not move, delete, recreate or
retag the immutable `v1.1.0` Git tag.

## Metadata policy after archive verification

Current citation/archive metadata records:

```text
version = 1.1.0
GitHub publication date = 2026-09-12
Git tag = v1.1.0
release SHA = 49588233ad2828b8fcc6140398ab55aedf7c03ef
Zenodo record = 22726717
DOI = 10.5281/zenodo.22726717
CITATION.cff date-released = 2026-09-12
.zenodo.json publication_date = 2026-09-12
```

`CITATION.cff` carries the verified version-specific DOI. `.zenodo.json` keeps the
archive publication date and records the Zenodo record/DOI in its notes while
remaining valid GitHub→Zenodo release metadata.

## Evidence custody

Public release evidence retains:

- publication SHA;
- workflow/run identity;
- final wheel/sdist and SHA-256 hashes;
- package/container audit evidence;
- release-prerequisite evidence;
- sanitized post-deploy scientific boundary;
- GitHub Release identity;
- Zenodo record identity and version-specific DOI.

Private SSH material, credentials and private scientific state are not part of
public release evidence.

See `docs/FINAL_SYSTEM_ACCEPTANCE.md`, `docs/SYSTEM_CLOSEOUT_MASTER.md`,
`docs/RELEASE_NOTES_1_1_0.md` and `docs/RELEASE_CHECKLIST.md`.
