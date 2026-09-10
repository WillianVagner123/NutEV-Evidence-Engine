# Product / tenant death-test report

2026-09-10. Status: **PASS for the existing hermetic core matrix; PENDING for the full product/browser acceptance**.

Evidence: GitHub Actions run 34537074947, source `bb2e93e43fab239e77039ae991934cfba13df513`, existing `tools/multitenant_death_test.py`; same CLI reproduced locally. Both report 17 passing checks, two tenants, two projects, one shared global article identity. Operational data were temporary synthetic fixtures, not production.

Verified matrix covers independent authentication/context, private search ownership, private placements and full-text grants, application boundaries, human-review assignment separation/submission locking, independent exports/audit chains and denied platform-admin private bypass. Assertions report no historical ownership change, scientific search, A1 modification or A2 binding modification.

This report does NOT extend those 17 checks to every requested browser/API case. Baseline Chromium workflow 34275598054 passed, but its existence does not prove a complete authenticated pilot flow or membership revocation semantics.

| Remaining scenario | State | Required evidence |
|---|---|---|
| Two authenticated browser users with own workspaces | PENDING | Browser traces with fixture IDs and version |
| Same-user two projects and two tabs | PENDING | Context isolation after tab switch, delayed response, reload |
| Back/forward and copied foreign deep links | PENDING | No old project state or unauthorized payload |
| Session expiration/logout/revocation | PENDING | Immediate server-side denial and client state cleanup |
| Every visible action / errors / empty/loading states | PENDING | Route/action census and deterministic expected outcomes |
| Desktop/mobile layout and accessibility | PENDING | Screenshots and keyboard interaction checks |
| Fresh generic client independent of Willian | PENDING | End-to-end synthetic application/search/library/review/export journey |

Existing core PASS is useful evidence, not authorization to execute destructive tests on production or a claim that all of phase 4 is closed.
