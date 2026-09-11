# Pre-SSH acceptance — 1.1.0 candidate

This is a code/package/rehearsal gate, not a production or publication certificate.
The active candidate remains PR #1246. Final exact-SHA results must be read from
its checks and the dated verification comment; no earlier green is inherited.

## Executed evidence before final candidate verification

Baseline 30f641: 1,045 local tests PASS. Publication hardening b6d9b4: 1,078 local
tests PASS and all seven PR workflows PASS. Build run 34553357429 executed clean
wheel/sdist builds, twine validation, archive-policy audit, isolated installation
outside the checkout and actual Docker privacy/runtime/recovery tests. Downloaded
artifacts were independently hash-checked and the package audit was rerun.

The next reviewed source changes add package-version checking to the actual HTTP
smoke, remove the private A1 topic-profile default from the generic CLI and add
an actual workflow-function recovery rehearsal with a deliberately failing
container. Local full suite: 1,083 PASS, no failures/skips. The newly added
container fault-injection rehearsal still requires the final CI execution; its
presence is not a PASS. Final results belong in the immutable audit artifact and
PR verification comment, avoiding an endless commit-to-record-own-SHA cycle.

## Corrected, reproduced defects

- Snapshot hashes previously ignored empty-directory deletion/addition, modes
  and ownership. Five failing regressions now pass with snapshot schema 2.
- Docker previously admitted arbitrary untracked runtime/backup directories.
  The source-root allowlist and nested exclusions passed five injected-canary
  tests in Docker, without using real secret data.
- Deployed version was a short Git SHA rather than the semantic package version.
  The deployment line is executed by a regression; HTTP version must now match.
- Generic science-topics silently selected the private A1 profile. It now requires
  an explicit user-supplied profile. The v1.0.0 CLI was checked: it exposed only
  help/version/providers, so no published v1.0.0 topic-command contract is removed.

## Conditions for READY_FOR_FINAL_RUNTIME_STAGE

Require the new candidate's seven workflows, including both Chromium jobs,
actual container build/privacy/recovery, package audit, isolated installation and
all required tests. Complete automated code review and retain the exact source
and artifacts. A review by the implementing agent is not independent human review.

The pass is scoped to the declared supported product and synthetic test cases.
It is not an exhaustive security/privacy certificate, live external-provider
availability test, all-filesystem ACL/xattr restoration guarantee or acceptance
of every historical/optional scientific UI. Future-scoped PRs remain outside this
release; do not merge them simply to clear the list.

## Final runtime dependencies intentionally not bypassed

Trusted SSH access and host identity; actual pilot configuration; real source
ownership; writers/quiescence/disk verification; production-volume reconciliation;
compatibility of the real backup and previous image; main-SHA gates; live HTTPS
and authorized tenant smoke. A1 approvals and A2 provenance remain separate.
No public tag, GitHub Release or archive deposit is authorized by a synthetic
container PASS alone. Final system acceptance remains NOT RELEASE COMPLETE.
