# Final system acceptance

Audit: 2026-09-10 (America/Sao_Paulo), PR #1246.

**Decision: NOT RELEASE COMPLETE. Code closure has advanced with executed isolated evidence; SSH/production acceptance is intentionally the final stage.**

## Implemented and tested

Exact-SHA release prerequisites; authenticated pilot route restrictions; stale-context write and response protection; cross-tab/logout expiry cleanup; export-render race correction; server-managed private A1 source-owner guard; quiesced snapshot/SQLite-WAL restoration checks; strict host pinning and previous-image/configuration recovery linkage.

Local final code suite: 1,044 tests PASS, no failures/skips, Python 3.13.5. The five private A1 source-owner regressions are included. Chromium run 34544938250 passed twelve authenticated scenarios on 5b7970373ef0dc49581ad742838e982c23605767 before the final A1 patch; all seven workflows for that head succeeded. Final-head results are recorded by #1246 checks and the dated verification comment; prior greens do not automatically transfer to a new commit.

The 17-check reusable engine matrix, 26 HTTP tests, 8 snapshot tests, 4 operation-linkage tests, deterministic export race test and 5 A1 ownership tests have explicit scope. This is not proof of all conceivable UI interactions, externally available providers, self-service signup or all optional scientific modules. Some legacy unscoped scientific APIs are deliberately unavailable in pilot until safely adapted.

## What was not done

No main merge, SSH credential change, server connection, deployment, real-volume reconciliation, historical ownership assignment, A2 binding, A1 academic approval, formal literature search or PRISMA generation. No real source data or protected full text was committed. #1128 alone was closed after patch comparison proved supersession; other old proposals were not blindly merged or removed.

## Remaining acceptance

Final candidate review/checks; secure SSH and trusted host identity; actual pilot/container/HTTPS version verification; real quiesced backup and rollback compatibility; production integrity reconciliation; reviewed A1 owner mapping and A2 legacy provenance. A1 PRESS/GF-10/D-132 approvals require the appropriate humans and remain independent scientific gates.

A1/A2 scientific blocking can coexist with a later accepted generic platform release if privacy and actual runtime acceptance are proven. Neither application may be falsely marked scientifically complete to obtain a green closeout. The final release designation requires its exact main SHA and actual deployed proof, not merely this document.
