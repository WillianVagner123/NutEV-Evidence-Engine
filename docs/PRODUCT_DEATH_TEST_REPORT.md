# Product / tenant death-test report

Audit: 2026-09-10 (America/Sao_Paulo). **PASS for the named synthetic core, HTTP and authenticated-browser scenarios. Production acceptance remains pending.**

## Executed browser evidence

Head `5b7970373ef0dc49581ad742838e982c23605767`, workflow 34544938250. PR checkout used synthetic merge `ed47633c32daa200530c18dd079689febdf356ac`. Artifact 10178673993, SHA-256 `29eb42947d53bb89d203652834cd840c53791408baa862338f6f570bbe8824df`.

The real Chromium matrix uses two independent browser contexts/users, two workspaces, three projects and one shared synthetic bibliographic article. It runs the real pilot HTTP server with temporary output paths and external providers disabled. No production URL or volume is accepted by the fixture CLI.

All twelve scenarios passed:

1. Two users log in and select their own workspace/project through the UI.
2. The same global article identity has private placements/notes.
3. The full-text permission/empty state renders without inferring access rights.
4. Changing project in one tab invalidates the other tab.
5. A copied foreign project parameter, back navigation and reload do not adopt foreign context.
6. A delayed old-context response cannot paint after context changes.
7. Export manifest and authorized download work; foreign download fails.
8. Pilot search page and its enabled action load.
9. Mobile menu works at 390px without horizontal overflow; desktop screenshot at 1366px.
10. Logout redirects both tabs and clears visible private state.
11. Expired server session clears visible private content.
12. No unexpected JavaScript page errors.

Screenshots, network-event metadata, page errors and fixture server logs are in the artifact. No credentials or request bodies are included in network metadata. The search-page assertion is NOT a live external-provider search or a complete keyboard/accessibility audit.

## HTTP and reusable-engine evidence

`test_pilot_http_closeout.py`: 26 passing cases covering malformed/encoded paths, legacy source/science denial, HEAD, cross-origin/form writes, foreign placement read/delete, foreign export/manifest, context-lease mismatch, logout, session expiry, membership removal and platform-admin non-bypass. A real offline search job completes with providers explicitly skipped; foreign job/search IDs fail closed. It does not fabricate scientific search results.

The existing reusable-engine matrix passes 17 checks, including HumanReviewEngine assignment separation, submission locks and private full-text grants. It complements rather than duplicates browser coverage. The 5 final A1 source-ownership cases verify that a writable application label cannot authorize a private first-party source.

## Defects found rather than hidden

Initial Chromium attempt timed out on network-idle readiness in a polling application. Readiness now uses DOM load plus explicit expected UI state. The next attempt passed six scenarios and exposed an actual race: overlapping initial/manual export loads erased a newly opened manifesto. `exports-page.js` now rejects stale render generations, locks refresh/manifest controls during loading and discards detached-panel responses. A deterministic Node regression executes the production JS module with reversed async completion; Chromium then passed the same manifest assertion.

Existing legacy browser coverage remains green independently. These checks do not certify every optional/legacy scientific UI, self-service account provisioning, live provider credentials or production access. Legacy unscoped scientific APIs are intentionally unavailable in pilot; their old presence is not a reason to weaken authorization.
