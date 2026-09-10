# NutEV System Closeout Master

Audit: 2026-09-10, America/Sao_Paulo. Execution PR: #1246, branch `closeout/release-gates-20260910`.
Baseline main: `0c354e23150f74692cd623007c5acc27a93fe28b`.
Code candidate before this documentation commit: `c45e302a3a8cdbac3b8721fe6020320aebd9e98f`.
Overall: **PENDING / NOT RELEASE COMPLETE**. This ledger is not a scientific approval or deployment authorization.

## Boundaries

No feature, vocabulary, scoring, scientific-state or historical ownership expansion. Global bibliographic identity stays separate from private project state. UNKNOWN is not migrated. Destructive tests run only in temporary synthetic fixtures; production checks must be non-destructive. No private key, protected full text or production database belongs in this repository.

Allowed states: PASS, FAIL, BLOCKED_EXTERNAL, BLOCKED_SCIENTIFIC, NOT_APPLICABLE, PENDING. PASS is scoped to evidence and exact code; any new commit requires fresh candidate CI. A PR success does not establish production success.

## Evidence matrix

| Requirement | State | Evidence / command | Source | Blocker / owner | Next gate |
|---|---|---|---|---|---|
| Baseline main identity | PASS | Branch read returned baseline SHA | CLOSEOUT_BASELINE.md | None | Revalidate before promotion |
| Baseline Python 3.12/3.13, Windows, blocking Ruff, scoped typing, guardrails | PASS | CI run 34275597931 | .github/workflows/ci.yml | Baseline only | Fresh candidate checks |
| Baseline Chromium / CodeQL | PASS | Runs 34275598054 / 34275598024 | CLOSEOUT_BASELINE.md | Not full pilot UX proof | Candidate and pilot-specific audit |
| Local candidate test suite | PASS | `PYTHONPATH=src python -m pytest -q nutev_tests`: 999 passed, Python 3.13.5 | CLOSEOUT_BASELINE.md | Exact source archive plus declared overlays; not production | CI on final candidate |
| Release verifier and workflow contracts | PASS | 84 targeted tests; 4 YAML files; 14 shell syntax checks | SECURITY_RED_TEAM_CLOSEOUT.md | Real GitHub promotion not executed | Candidate CI and reviewed promotion |
| Existing hermetic multi-tenant matrix | PASS | 17 checks locally and run 34537074947 on bb2e93e43fab239e77039ae991934cfba13df513 | PRODUCT_DEATH_TEST_REPORT.md | Limited to implemented matrix | Browser/API cases not covered remain pending |
| Pre-deploy aggregate barrier defect | PENDING | Corrected in candidate code, not main or production | tools/check_release_prerequisites.py | PR #1246 review and exact-SHA checks | Merge only reviewed candidate |
| SSH configuration | BLOCKED_EXTERNAL | Deploy 34275710592 attempt 3 failed Configure SSH | PRODUCTION_SMOKE_REPORT.md | Owner: HETZNER environment secret | Correct secret securely, never in chat |
| Production deploy/auth/SHA/edge | BLOCKED_EXTERNAL | No successful candidate deployment or authenticated runtime inspection | PRODUCTION_SMOKE_REPORT.md | SSH + acceptance gates | pilot + internal/public smoke + exact SHA |
| Full pilot browser journey | PENDING | Baseline Chromium is not all requested cases | PRODUCT_DEATH_TEST_REPORT.md | Authenticated synthetic test fixture | Multi-tab/reload/deep-link revocation matrix |
| Production integrity / recovery | PENDING | No volume inspected or modified; source archive verified | DATA_INTEGRITY_CLOSEOUT.md; ROLLBACK_RUNBOOK.md | Runtime access and reviewed backups | Read-only reconciliation + restore rehearsal |
| A1 authorization | BLOCKED_SCIENTIFIC | Repository PRESS/GF-10/freeze gates not approved; D-132 proposal only | ARTICLE1_FORMAL_GATE_STATUS.md | Academic governance and named human verifier | Retrieve canonical approvals; never fabricate |
| A2 binding | BLOCKED_EXTERNAL | No actual production inventory or validated ownership evidence | ARTICLE2_LEGACY_BINDING_AUDIT.md | Runtime access, reviewed mapping | Inventory then validated binding |
| Open PR initial classification | PASS | 46 pre-existing IDs inventoried; 4 BLOCKED, 42 FUTURE_BACKLOG | OPEN_PR_DISPOSITION.md | Patch-level disposition still pending | No blind merge or closure |
| Final acceptance | PENDING | No final accepted deployment | FINAL_SYSTEM_ACCEPTANCE.md | Above blockers | Independent acceptance |

## Order

P0: secure SSH configuration and enforce reviewed release barrier. P1: candidate CI, pilot security/UX, production identity, backup/restore and data reconciliation. P2: A1 academic gates and A2 provenance. P3: legacy PR patch review and documentation alignment. A scientific blocker does not prevent safe platform work, but it cannot be marked PASS to simplify closeout.

## Audit environment

Initial direct GitHub/network DNS failed. Source access was subsequently recovered through the connector's GitHub Actions artifact, not by bypassing authentication. The exact tracked source archive was verified and extracted; local tests then executed. This is an archive with explicit overlays, not a claim of a full git clone or live production access. See CLOSEOUT_BASELINE.md for identity and failure-history details.

## Reports

CLOSEOUT_BASELINE.md; OPEN_PR_DISPOSITION.md; PRODUCT_DEATH_TEST_REPORT.md; DATA_INTEGRITY_CLOSEOUT.md; ARTICLE2_LEGACY_BINDING_AUDIT.md; ARTICLE1_FORMAL_GATE_STATUS.md; SECURITY_RED_TEAM_CLOSEOUT.md; PRODUCTION_SMOKE_REPORT.md; ROLLBACK_RUNBOOK.md; FINAL_SYSTEM_ACCEPTANCE.md. Detailed CI results on newer commits belong in the PR/check URLs, not silently retrofitted into this baseline.
