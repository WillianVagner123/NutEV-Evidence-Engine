# NutEV System Closeout Master

Audit closeout date: 2026-09-12, America/Sao_Paulo.

Immutable software release identity:

```text
version = 1.1.0
tag = v1.1.0
sha = 49588233ad2828b8fcc6140398ab55aedf7c03ef
GitHub Release = PUBLISHED
Zenodo record = 22726717
Zenodo DOI = 10.5281/zenodo.22726717
```

Overall software state:

```text
PRODUCTION ACCEPTED
GITHUB RELEASED
ZENODO ARCHIVED
PUBLICATION CLOSEOUT COMPLETE
```

## Immutable boundaries

Never fabricate counts, provider results, identifiers, human reviews, PRESS/GF-10
approval, A2 `LegacyBindingEvidence` or PRISMA state. Do not reassign historical
scientific ownership by inference. Global bibliographic identity is distinct from
private search/project/review state. UNKNOWN remains unbound.

Published tags `v1.0.0` and `v1.1.0` are immutable and must not be moved. The
historical DOI `10.5281/zenodo.21998607` belongs only to `v1.0.0`; the verified
version-specific DOI for `v1.1.0` is `10.5281/zenodo.22726717`.

PASS always names a SHA, environment and scope. CI, deploy, package publication,
archive publication and scientific approval are separate gates.

## Final release evidence

The exact `v1.1.0` publication SHA completed:

```text
7/7 required workflows on exact SHA
  -> exact-SHA release prerequisites
  -> recovery readiness
  -> trusted SSH / host identity
  -> 80/443 ownership inventory
  -> protected snapshot / recovery rehearsal
  -> production deploy
  -> version and public/private smoke
  -> read-only doctorate runtime audit
  -> immutable Git tag
  -> GitHub Release + audited assets
  -> Zenodo integration sync
  -> version-specific archive + DOI verification
```

The first deployment attempt encountered a transient SSH `Broken pipe` after the
preflight had passed. The same exact-SHA deployment job was rerun without code or
gate changes and completed successfully on attempt 2. No release tag was created
while deployment was failed.

## Runtime acceptance

The final release runtime was accepted with:

- semantic package version `1.1.0`;
- deployed commit identity `49588233ad2828b8fcc6140398ab55aedf7c03ef`;
- `NUTEV_AUTH_MODE=pilot`;
- public web smoke passing;
- private scientific surfaces fail-closed without authentication;
- existing host-level Caddy preserved;
- platform schema initialized without inventing scientific applications;
- post-deploy doctorate audit successful and read-only.

The post-deploy audit verified:

```text
read_only = true
scientific_state_modified = false
legacy_binding_performed = false
search_executed = false
A1 ResearchApplications = 0
A2 ResearchApplications = 0
```

## Requirement ledger

| Requirement | Final state | Boundary |
|---|---|---|
| Core tests, identity, HTTP isolation and guardrails | PASS | Exact release SHA |
| Authentication/browser lifecycle | PASS | Tested contracts only |
| Multi-tenant project/review separation | PASS | Exact release SHA |
| Dependency review | PASS | Exact release SHA |
| Security scan | PASS | Exact release SHA |
| CodeQL | PASS | Exact release SHA |
| Release artifact validation | PASS | Exact release SHA |
| Python wheel/sdist public boundary | PASS | Audited artifacts attached |
| Container privacy/recovery | PASS | Audited evidence attached |
| Recovery capacity/retention | PASS | Production gate |
| Existing Caddy preservation | PASS | Host-level proxy external |
| Production deployment | PASS | `49588233...` |
| Post-deploy doctorate audit | PASS | Read-only; 0 A1/0 A2 |
| Git tag `v1.1.0` | PUBLISHED | Points exactly to `49588233...` |
| GitHub Release `v1.1.0` | PUBLISHED | Stable, not draft/prerelease |
| Zenodo/archive record `v1.1.0` | PUBLISHED | Record `22726717` |
| DOI `v1.1.0` | VERIFIED | `10.5281/zenodo.22726717` |
| A1 scientific gates | BLOCKED_SCIENTIFIC | Human/academic evidence required |
| A2 historical binding | BLOCKED_PROVENANCE / BLOCKED_SCIENTIFIC | Real reviewed provenance required |

## Public release assets

The GitHub Release preserves:

```text
nutev_nutmev-1.1.0-py3-none-any.whl
nutev_nutmev-1.1.0.tar.gz
distributions.json
SHA256SUMS.txt
release-evidence.json
container-audit.zip
release-prerequisites.zip
```

The release controller verified the exact SHA, required workflow runs, successful
production deploy, successful post-deploy auditor and artifact identities before
creating the tag/release.

The GitHub↔Zenodo integration subsequently synchronized the repository and the
repository owner confirmed the public `1.1.0` archive identity as Zenodo record
`22726717`, DOI `10.5281/zenodo.22726717`.

## Scientific separation

A1 and A2 are private consumers of the generic platform, not hidden defaults of
the Engine.

A1 remains subject to its academic methodology contracts. A2 remains dark/fail-
closed until provenance is sufficient for reviewed binding. GitHub/Zenodo
publication does not promote the general scientific validation state, which
remains:

```text
B — DEMOTE
```

## Publication closeout

The public software publication is complete:

```text
GitHub v1.1.0 = RELEASED
Zenodo v1.1.0 = ARCHIVED
Zenodo record = 22726717
DOI v1.1.0 = 10.5281/zenodo.22726717
```

No public software publication gate remains open for `v1.1.0`. Future commits on
`main` may maintain documentation or software, but they must not move, delete or
recreate the immutable `v1.1.0` tag.

Use `docs/FINAL_SYSTEM_ACCEPTANCE.md`, `docs/PUBLICATION_READINESS.md`,
`docs/RELEASE_NOTES_1_1_0.md` and `docs/RELEASE_CHECKLIST.md` together for the
release record.
