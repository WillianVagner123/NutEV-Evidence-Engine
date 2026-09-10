# Rollback runbook — acceptance prerequisites

2026-09-10. **PENDING: no actual production restore rehearsal performed.** Do not read this document as a tested recovery guarantee.

## Existing implementation and gaps

The inherited deploy workflow tags the previous container image as nutev:rollback and attempts to start it if selected gates fail. Its health probe is non-blocking; it does not establish restoration of the previous compose/configuration or database compatibility. A code-image rollback is not a scientific-data rollback. The current closeout patch preserves this tail and does not claim those gaps fixed.

## Required before production acceptance

Record the old deployed SHA, immutable image ID/digest, compose/configuration version, database schema versions, volume identity, backup artifact hashes and retention location in an access-controlled operations record. Do not copy secret .env contents or scientific payloads into public Git.

Create a consistent backup using a method appropriate to each database (including SQLite journal/WAL consistency); test restoration into an isolated environment. Reconcile counts/hashes/foreign keys/audit chains and verify authorized project access against the restored data. Explicitly record migrations that are irreversible or require forward recovery.

For a failed code-only promotion with compatible data, restore the exact previous image and reviewed configuration; verify health, exact version, authentication mode, project boundaries and HTTPS. For any schema/data change, use the reviewed compatibility/restore plan, not an automatic destructive downgrade. Preserve post-backup human decisions and investigate them before any restore.

Stop promotion on a missing backup, unverified host identity, unknown migration reversibility, unsuccessful restore rehearsal or inability to prove old/new version identity. Never run docker volume deletion, blanket data reset, raw historical replay or UNKNOWN ownership activation as rollback.

No rollback or backup deletion was executed in this audit. Operational values remain unfilled because production was not accessed; they must not be guessed from repository defaults.
