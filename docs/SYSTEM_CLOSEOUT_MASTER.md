# NutEV System Closeout Master

Audit date: 2026-09-10, America/Sao_Paulo. Active PR #1246:
`closeout/release-gates-20260910`. Main baseline:
`0c354e23150f74692cd623007c5acc27a93fe28b`.

Candidate version: **1.1.0, UNPUBLISHED**. Overall **NOT RELEASE COMPLETE**.
SSH, trusted host configuration and actual production acceptance are the final
operational stage by owner instruction. This master defines scope; immutable
final execution results are in the exact-SHA PR checkpoint and audit artifacts.

## Immutable boundaries

No fabricated counts, provider results, identifiers, human reviews, PRESS/GF-10
approval, A2 LegacyBindingEvidence or PRISMA. No production data mutation or
historical reassignment. No scoring/taxonomy/query expansion. Global bibliography
is distinct from private search/project/review state. UNKNOWN stays unbound.
Published tags, including v1.0.0, remain unchanged.

PASS always names a SHA, command, environment and test scope. PR head, tested
synthetic merge, final main, image identity and package hashes are distinct.
A new commit needs new CI; never transfer an earlier aggregate PASS silently.

## Verified execution history

- Prior 30f641 candidate: 1,045 local tests, original tenant/browser/recovery gates.
- Publication hardening b6d9b40768afcdd3a43edf49e6becde5398f8e45:
  1,078 local tests; all seven PR workflows completed successfully.
- Run 34553357429 built and audited wheel/sdist, installed the wheel outside the
  source checkout and executed actual Docker context/privacy/runtime/metadata
  recovery checks. Artifact hashes were verified after download and package
  inspection was rerun independently in the audit container.
- Current follow-up local source: **1,083 tests PASS**, Python 3.13.5, no
  failures/skips. It adds actual workflow rollback fault injection, semantic
  runtime-version checking and an explicit generic CLI topic-profile requirement.
  Final remote checks for that follow-up must be read from the PR checkpoint.

Local evidence preserves failing-before/fixed-after regressions. The five
filesystem metadata cases failed before the fix; the short-SHA version and
implicit private A1 topic default also failed their new regressions before fixes.
Test subsets are not added to full-suite totals. Docker/browser counts are
separate scenarios, not an exhaustive safety or scientific-validity claim.

## Requirement ledger

| Requirement | Executed scope / state | Evidence / next gate |
|---|---|---|
| Core tests, identity, HTTP isolation and scientific guardrails | Local PASS; final-head remote rerun required | 1,083 tests; CI checks on actual candidate |
| Authentication, two users/tabs, stale responses, export lifecycle | Existing real Chromium matrices; new candidate must rerun | predeploy-browser-e2e, both required jobs |
| Shared identity and private state/review separation | 17-check hermetic matrix, plus HTTP and A1 regressions | multitenant-release-audit |
| Exact-SHA release prerequisites | Fail-closed tests and required jobs/steps | check_release_prerequisites.py; not a production approval |
| Python public package boundary | Actual wheel/sdist audit and isolated install PASS on b6d9b4 | Rebuild and recheck final artifact hashes |
| Docker private-data exclusion | Five injected canaries excluded, actual image PASS on b6d9b4 | Final container gate |
| Snapshot metadata/SQLite WAL | Schema 2; bytes, directories, modes, numeric uid/gid tested | 13 local cases plus actual Docker fixture |
| Real workflow recovery functions | New disposable fault-injection harness | Must execute final container CI; no static-only PASS |
| Generic engine independence | CLI private A1 default removed; explicit profile regression PASS | No released v1.0.0 CLI contract removed |
| Release version consistency | Candidate package/CFF/Zenodo 1.1.0, no new DOI/date claim | Runtime checker verifies package version separately from SHA |
| Repository/PR disposition | #1128 closed only on proven supersession; historical proposals scoped out | OPEN_PR_DISPOSITION.md; no blind merge/close |
| Real production data/owner bindings | BLOCKED_EXTERNAL | Actual read-only inventory and reconciliation after trusted access |
| Actual deployment and public acceptance | BLOCKED_EXTERNAL | SSH/host pin, real quiescence/backup, main-SHA gates, pilot/HTTPS smoke |
| A1 scientific gates | BLOCKED_SCIENTIFIC | Genuine academic verifier/PRESS/GF-10 records |
| A2 historical binding | BLOCKED_EXTERNAL | Real provenance and reviewed internal binding |
| Publication | PENDING | No tag/release/deposit until all applicable gates verified |

## Final stage and limits

`docs/PRE_SSH_ACCEPTANCE.md` controls readiness for server work. The source and
package audits certify stated checks, not unrestricted copyright/redistribution
of external papers, every historic repo object or every optional scientific UI.
ACLs/xattrs and production schema compatibility require explicit verification
when relevant. No new licensed-source access or live scientific search was run.
The local container cannot run Docker/browser; actual GHA evidence is identified
as such. No environmental access restriction was bypassed.

Use `docs/PUBLICATION_READINESS.md`, `docs/ROLLBACK_RUNBOOK.md`, the exact-SHA PR
checkpoint and `docs/FINAL_SYSTEM_ACCEPTANCE.md` together. Do not update this
ledger to PASS merely because the underlying code exists. Final machine-readable
execution evidence can live outside the source commit, avoiding an endless
commit-to-record-own-SHA cycle while preserving exact provenance.
