# NutEV System Closeout Master

Audit date: 2026-09-10 (America/Sao_Paulo). This is an evidence ledger, not a release approval.

Baseline: `main@0c354e23150f74692cd623007c5acc27a93fe28b` (PR #1245).
Working branch: `closeout/release-gates-20260910`.
Overall state: **PENDING / NOT RELEASE COMPLETE**.

## Scope and immutable boundaries

Freeze feature/vocabulary/scoring expansion. Preserve global bibliographic identity and private workspace/project/search/review state. No scientific search, production migration, historical ownership adoption, PRISMA event, human approval, or production-data mutation is authorized by this ledger. Destructive tests run only on temporary synthetic fixtures. Production smoke must be non-destructive.

Allowed states: PASS, FAIL, BLOCKED_EXTERNAL, BLOCKED_SCIENTIFIC, NOT_APPLICABLE, PENDING. PASS is scoped to the stated execution and SHA, never inferred from a file or PR title. A documentation commit invalidates any claim that the entire new release SHA has already passed CI.

## Baseline evidence

- Main ref: https://github.com/WillianVagner123/NutEV-Evidence-Engine/commit/0c354e23150f74692cd623007c5acc27a93fe28b
- CI: https://github.com/WillianVagner123/NutEV-Evidence-Engine/actions/runs/34275597931
- Chromium: https://github.com/WillianVagner123/NutEV-Evidence-Engine/actions/runs/34275598054
- Failed deployment, attempt 3: https://github.com/WillianVagner123/NutEV-Evidence-Engine/actions/runs/34275710592
- Deployment job: https://github.com/WillianVagner123/NutEV-Evidence-Engine/actions/runs/34275710592/job/102252237328
- CodeQL: https://github.com/WillianVagner123/NutEV-Evidence-Engine/actions/runs/34275598024

## Control matrix

All baseline CI entries below refer only to the baseline SHA above. Post-change verification is PENDING.

| Requirement | State | Evidence / command | Related file | Blocker / owner | Next gate |
|---|---|---|---|---|---|
| Revalidate main | PASS | Main branch API returned baseline SHA | AGENTS.md | None | Recheck before promotion |
| Python 3.12 / 3.13 CI | PASS | CI jobs 102227706267 / 102227706270 succeeded | .github/workflows/ci.yml | Baseline only | Rerun on candidate |
| Windows smoke | PASS | CI job 102227706318 succeeded | .github/workflows/ci.yml | Baseline only | Rerun on candidate |
| Blocking Ruff | PASS | CI job 102227706352 succeeded | .github/workflows/ci.yml | Advisory style uses `|| true`; not a style-clean claim | Rerun blocking checks |
| Provenance typecheck | PASS | CI job 102227705897 succeeded | .github/workflows/ci.yml | Covers three configured files, not whole repository | Preserve scope disclosure |
| Configured scientific guardrail jobs | PASS | CI job 102227706289 succeeded | .github/workflows/ci.yml | Does not establish human scientific approval | Rerun on candidate |
| Chromium pre-deploy | PASS | Run 34275598054 succeeded | .github/workflows/predeploy-browser-e2e.yml | Detailed browser coverage audit PENDING | Inspect jobs/artifacts |
| CodeQL Python | PASS | Check 102227706386 succeeded on baseline SHA | .github/workflows/codeql.yml | Baseline only | Rerun on candidate |
| Standalone Full Multi-tenant Death Test | PENDING | `python tools/multitenant_death_test.py` | docs/FULL_MULTITENANT_DEATH_TEST.md | Explicit executed report not yet obtained | Inspect and execute hermetically |
| Security scan / dependency review / release artifact validation | PENDING | Exact-SHA jobs to be inspected | .github/workflows/ | Do not substitute PR-head success for merge SHA | Reconcile execution applicability |
| Aggregate pre-deploy gate | FAIL | Workflow triggers only after `ci`; no other required-check barrier before SSH; manual dispatch also needs validation | .github/workflows/deploy-hetzner.yml | Release engineering | Add and test fail-closed exact-SHA barrier |
| SSH configuration | BLOCKED_EXTERNAL | Deployment job failed at Configure SSH before connection | docs/FINAL_MULTITENANT_RELEASE_GATE.md | Repository owner: HETZNER environment secret | Correct valid matching private key outside chat; never weaken validation |
| Production deploy | BLOCKED_EXTERNAL | Verify SSH / Deploy steps skipped in failed run | .github/workflows/deploy-hetzner.yml | SSH + release gates | Promote only verified SHA |
| Production auth mode / live SHA / local runtime smoke | PENDING | Not observed in this audit | deploy/hetzner/ | Authenticated runtime access required | Verify pilot and exact SHA |
| Public HTTPS smoke / version | PENDING | Audit environment could not obtain an HTTP response; not evidence of outage | docs/FINAL_MULTITENANT_RELEASE_GATE.md | Runtime access | Verify edge plus identity; 401 alone is insufficient |
| A1 scientific authorization | BLOCKED_SCIENTIFIC | Canonical master has PRESS not PASS, GF-10 false, freeze false | ARTICLE1_SEARCH_MASTER.md; config/nutev/article1_search_master_v1.json | Authorized academic reviewers | Record genuine approvals only |
| D-132 proposal | BLOCKED_SCIENTIFIC | PR #1230 remains draft / proposed | PR #1230 | Advisor and named human verifier | Review proposal without manufacturing approval |
| A2 historical binding | BLOCKED_EXTERNAL | Runtime inventory and reviewed provenance not available | docs/ARTICLE2_INTEGRATIVE_WORKFLOW.md | Runtime access + reviewed mapping | Read-only inventory; UNKNOWN stays unmigrated |
| Data reconciliation / backup restoration | PENDING | No production volume inspected or mutated | MULTITENANT_MIGRATION_INVENTORY.md | Runtime access | Hash/count reconciliation and tested recovery |
| All open PR dispositions | PENDING | Initial inventory contains historical expansions and separate bot updates | docs/OPEN_PR_DISPOSITION.md | Need complete reconciliation and patch review | No blind merge or close |
| Final acceptance | PENDING | No final RC, deployed identity or completed acceptance pack | docs/FINAL_SYSTEM_ACCEPTANCE.md | Above gates | Independent final review |

## Priority and execution order

1. P0 external: invalid deployment secret. Only the owner should correct `HETZNER_SSH_KEY` in the HETZNER environment, outside chat/logs/Git. Match its public half to the server's authorized key. Do not guess or replace server access automatically.
2. P0 release control: enforce the documented prerequisites for the exact target SHA before production access, including manual promotion. A green `ci` alone must not promote.
3. P1: independently verify tenant/privacy/browser coverage, production identity/auth, full data reconciliation and rollback.
4. P2: preserve A1 academic and A2 provenance gates; pending scientific work does not authorize platform shortcuts.
5. P3: classify legacy expansion PRs as future work when appropriate; do not change taxonomy/scoring to clean the PR list.

Continue isolated code/tests/documentation while external gates are blocked. No production retry solely to repeat an unchanged secret failure.

## Environment limitation

The current audit container has Python 3.13.5 and pytest, but no repository checkout, no agent-browser executable, and GitHub DNS resolution failed. GitHub connector reads/writes remain available. Any local test must identify the exact staged files and restricted scope; do not claim full-repository or production execution from it. No background completion is promised.
