# NutEV System Closeout Master

Audit: 2026-09-10, America/Sao_Paulo. PR #1246, branch `closeout/release-gates-20260910`.
Baseline main: `0c354e23150f74692cd623007c5acc27a93fe28b`.
Overall: **PENDING / NOT RELEASE COMPLETE**. SSH and production execution are deliberately deferred to the final operational stage at the owner's request.

## Boundaries and evidence scope

Freeze vocabulary/scoring/features. Preserve global bibliographic identity separately from private project state. UNKNOWN is not migrated. No production access, private key change, scientific search, A1 approval, A2 binding or historical-data mutation was performed.

States: PASS, FAIL, BLOCKED_EXTERNAL, BLOCKED_SCIENTIFIC, NOT_APPLICABLE, PENDING. PASS always names its execution scope; a new commit requires fresh CI. PR checkout can use a synthetic merge commit, so PR success does not prove the eventual main SHA or production image.

Most recent completed seven-workflow validation before the final A1 source-ownership patch: head `5b7970373ef0dc49581ad742838e982c23605767`. Runs: CI 34544938337; Chromium 34544938250; CodeQL 34544938246; dependency review 34544938344; security 34544938354; artifact validation 34544938360; tenant audit 34544938443. Final-head results must be read from #1246/checks, not inferred from these older runs.

## Control matrix

| Requirement | State and scope | Evidence | Remaining gate / owner |
|---|---|---|---|
| Full local candidate suite | PASS: 1,044 tests, Python 3.13.5 | `PYTHONPATH=src python -m pytest -q nutev_tests`; full-tests-final.xml, includes final A1 patch | Fresh final-head CI |
| Exact-SHA promotion barrier | PASS in regression tests; not executed against production | tools/check_release_prerequisites.py; 84 targeted verifier/linkage cases within suite | Final main-SHA verification |
| Existing reusable tenant/review engine | PASS: 17 hermetic checks | tools/multitenant_death_test.py; multitenant-release-audit | Controlled real-runtime smoke at final stage |
| Pilot HTTP boundary | PASS: 26 fixture tests | test_pilot_http_closeout.py | Production configuration and live identity |
| Authenticated Chromium | PASS: 12 named scenarios | Run 34544938250, pilot-browser artifact; PRODUCT_DEATH_TEST_REPORT.md | Rerun final candidate; no claim of all future features |
| Export response race | PASS after reproducing and fixing actual UI race | Production exports-page.js; deterministic Node regression; Chromium export scenario | Final candidate CI |
| Private A1 source ownership | PASS: 5 local regressions including real HTTP forged-configuration denial | test_first_party_source_ownership.py | Reviewed runtime owner pins, never guessed; final CI |
| Snapshot and restore | PASS: 8 synthetic cases, including committed SQLite WAL | test_recovery_snapshot.py; recovery_snapshot.py | Actual quiescence/disk/volume/compatibility proof after SSH |
| Host identity / deployment linkage | PASS: 4 static contracts; no connection made | test_closeout_operations_boundary.py | Verified HETZNER_KNOWN_HOSTS in final setup |
| Final PR CI | PENDING until final head checks complete | #1246 checks and dated evidence comment | CI / code reviewer |
| SSH / production / live SHA / pilot auth / edge | BLOCKED_EXTERNAL, deferred by owner | PRODUCTION_SMOKE_REPORT.md | Final operational stage, not a code-test bypass |
| Production reconciliation | BLOCKED_EXTERNAL | DATA_INTEGRITY_CLOSEOUT.md | Real read-only inventory and before/after reconciliation |
| A1 methodology | BLOCKED_SCIENTIFIC | ARTICLE1_FORMAL_GATE_STATUS.md | Academic governance, named human verifier, PRESS/GF-10 |
| A2 legacy binding | BLOCKED_EXTERNAL | ARTICLE2_LEGACY_BINDING_AUDIT.md | Reviewed provenance from actual runtime |
| Legacy PR disposition | Partial completion, not universal patch approval | OPEN_PR_DISPOSITION.md; #1128 closed unmerged as superseded | Remaining out-of-scope proposals preserved |
| Final system acceptance | PENDING | FINAL_SYSTEM_ACCEPTANCE.md | Verified main release and real-runtime acceptance |

The 26 HTTP, 8 recovery, 5 A1, 4 operations and targeted release tests are subsets of the 1,044, not extra counts. Browser/core scenario counts are separate executions, not proof of exhaustive coverage or external-provider availability.

## Final operational sequence

Finish code review and final PR tests before touching SSH. Then verify host pin and credential through trusted configuration, inspect real owner mappings/readiness, approve a controlled main promotion, require all checks on that exact main SHA, take and rehearse a quiesced snapshot, deploy and verify pilot/auth/version/internal/HTTPS surfaces. No merge or deploy has been performed by this closeout execution. Scientific approvals remain independent and cannot be replaced by green software tests.

The local browser was blocked by environment policy; it was not bypassed. The real Chromium evidence comes from GitHub Actions using temporary data. Reports contain no private production payload or secrets.
