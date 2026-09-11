# Final system acceptance — 1.1.0 candidate

**Decision: NOT RELEASE COMPLETE / NOT PUBLISHED.**

This release closeout has executed code, package and isolated-runtime audits.
It has not deployed to the real server or published a new release/DOI. The
current source is held in PR #1246; final outcomes must be read for its exact
head and tested merge SHA, not copied from an older green run.

## Implemented

Multi-tenant HTTP and source-ownership boundaries; stale browser/tab/logout
protection; export race correction; exact-SHA workflow/step enforcement;
explicit Python and Docker package boundaries; artifact inspection and isolated
wheel installation; snapshot bytes/directory/mode/uid/gid verification; required
Docker runtime and workflow-recovery fault injection; consistent semantic package
version; explicit user-selected profile in the generic topic CLI.

## Executed evidence

Full latest local source suite: 1,083 PASS on Python 3.13.5. Earlier publication
candidate b6d9b4 completed all seven PR workflows. Its wheel/sdist, clean isolated
install, Docker build/private-canary exclusion, pilot runtime and numeric-owner
recovery checks passed. Artifacts were downloaded, hash-checked and re-audited.
The final source change extends the Docker check to execute actual workflow
recovery functions with an intentionally failing image and requires a fresh CI
run. The verified final PR comment and audit manifest record those final results.

These are scoped technical results, not scientific validation, external-provider
availability, actual-server recovery or a guarantee for all historical modules.
The repository scientific validation state is not promoted by software tests.

## Remaining final operational acceptance

Trusted server access and host identity; real configuration and data ownership;
all-writer quiescence/disk capacity; production backup/schema compatibility;
controlled merge and exact-main-SHA gates; actual deployment; live pilot and HTTPS
version/isolation verification; real data reconciliation; final artifact/tag
publication and archive confirmation. No private key or owner mapping is guessed.

A1 human methodology and A2 reviewed legacy provenance remain independent gates.
They may remain blocked in an otherwise accepted generic platform release, but
must stay private and must not be described as scientifically completed.

## Publication identity

Candidate 1.1.0 preserves the package name and the released v1.0.0 CLI contracts.
The old v1.0.0 tag/DOI remains unchanged. Candidate CFF/Zenodo metadata has no
fabricated release date or new DOI. CI artifacts are not public releases.
A GitHub source archive and a Python wheel have different content scopes; their
audit records must identify the exact distribution being approved.

See SYSTEM_CLOSEOUT_MASTER.md, PRE_SSH_ACCEPTANCE.md and PUBLICATION_READINESS.md.
Final green PR checks do not override the operational requirements above.
