# Security red-team closeout

2026-09-10 (America/Sao_Paulo). **Named regression tests PASS. No claim of exhaustive security or production verification.**

## Corrected findings

### Release prerequisites

The inherited deploy waited only for `ci`, despite a broader documented contract. The exact-SHA verifier now requires seven trusted workflow paths, required jobs and successful steps; it rejects old/fork/PR/missing/failed/skipped/superseded evidence and rechecks after environment approval before SSH. The authenticated pilot browser job is also mandatory. Existing 84 verifier/linkage cases are a subset of the full suite.

### Unscoped legacy HTTP surfaces

Pilot dispatch now canonicalizes paths before legacy handlers and fails closed on unknown APIs, private/source files, ambiguous encoded separators and dot segments. Legacy scientific/Workbench/loopback authorization is not accepted as tenant authorization. Known private routes still perform service-level authorization. JSON write Origin/Host/site constraints reject cross-origin and form submissions. Private responses are not cacheable. Twenty-six real HTTP fixture cases passed.

### Stale browser context and export race

Client context headers constrain, never grant, server access. Other tabs, logout and delayed old-context responses invalidate stale UI. Only random non-private invalidation signals are broadcast/stored. Visible pages recheck a short lease; server-side expiry/revocation is enforced on requests. A separate actual export-render race was fixed in production JS and verified with deterministic Node execution and real Chromium. Twelve authenticated browser scenarios passed in run 34544938250.

### A1 source-ownership impersonation

A synthetic regression demonstrated that setting an editable application configuration to `SCOPING_REVIEW / WILLIAN_DOCTORATE_A1` could previously satisfy the private static-source guard. This is evidence of a code authorization defect, NOT evidence of a production leak.

The guard and D-132 owner/guest adapters now require server-managed `NUTEV_A1_WORKSPACE_ID` and `NUTEV_A1_PROJECT_ID`, in addition to existing membership/application/guest authorization. Missing, malformed or foreign pins deny before loading the private source. Existing guest credentials must also belong to that source owner. The pins are populated only from reviewed real-runtime ownership evidence; no actual IDs were guessed or configured here. This does not approve D-132, PRESS or GF-10. Five regressions passed, including forged configuration over real HTTP.

### Recovery and host identity

SSH secrets are scoped to their necessary steps. Live `ssh-keyscan` trust was replaced with a separately verified `HETZNER_KNOWN_HOSTS` pin and strict host checking. A protected quiesced snapshot and isolated restore proof precede image replacement; rollback uses the prior immutable image/configuration and checks its exact version. Eight snapshot tests and four static deployment-linkage tests passed. No SSH connection or Docker production rollback was executed.

## Failure history and remaining boundary

The first clean CI run exposed missing PyYAML and an unused test import. The dependency is now explicitly pinned in CI and the import removed; no test was weakened. Browser readiness and export race failures were investigated and preserved as evidence rather than labelled flaky or skipped.

The full local suite including the final A1 fix reports 1,044 PASS. The last completed seven-workflow set before that final fix belongs to head 5b7970373ef0dc49581ad742838e982c23605767; final head needs new checks. Remaining acceptance requires reviewed real-runtime owner bindings, host identity, production auth/version/isolation, actual backup/restore compatibility and current provider credentials. Scientific approval is independent of security tests.
