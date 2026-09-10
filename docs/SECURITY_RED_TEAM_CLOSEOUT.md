# Security red-team closeout

2026-09-10. **Scoped code tests PASS; full application/production security acceptance PENDING.**

## Finding and correction

P0 release-control defect: deploy-hetzner depended only on ci, while documented prerequisites included independent CodeQL/Chromium/security/dependency/artifact gates. Manual deployment also lacked the aggregate check. Timing of baseline runs corroborates the race: deploy queued before independent Chromium/CodeQL completion. The actual deployment stopped at SSH configuration, so this is not evidence an unsafe image was promoted.

Candidate c45e302a3a8cdbac3b8721fe6020320aebd9e98f adds an explicit dependency barrier and rechecks after environment approval before reading the SSH key. Key environment scope is restricted to configuration steps. The verifier requires current main, exact SHA/repository/workflow paths, trusted push/manual runs, latest attempts, successful required jobs and real required-step completion. PR/fork/stale/failed/skipped/missing executions cannot satisfy it. API redirects and malformed/incomplete pagination fail closed. No API error bodies or secrets are echoed.

Executed: 59 synthetic verifier cases plus 25 workflow/ref-resolution contracts = 84 PASS. They cover target validation, older green/newer red runs, manual bypass, changing main, changing attempts, newly dispatched runs, hidden failed steps, API pagination, redirected requests, missing token, exact workflow names and immutable dependency refs. These are synthetic API tests, not a live production promotion.

Existing core tenant matrix: 17 PASS locally and in run 34537074947. Full suite: 999 PASS using canonical command. None proves every HTTP route or browser state boundary secure.

## Remaining P1 work

Audit actual pilot HTTP authorization, encoded paths, static A1 context, legacy endpoints, guest revocation/expiry, CSRF/session behavior, delayed cross-project responses and multi-tab state. Validate host key independently: current inherited SSH setup uses ssh-keyscan without a separately verified pin. Prove backups and recovery; inherited rollback checks are not comprehensive. Assess current dependencies/CodeQL findings on candidate. These items remain open, not silently waived by this patch.

No attack was run against production, no foreign real tenant was accessed, and no production credential was exposed.
