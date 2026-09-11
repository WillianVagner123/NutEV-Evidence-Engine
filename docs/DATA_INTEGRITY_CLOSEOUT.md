# Data integrity closeout

2026-09-10 (America/Sao_Paulo). **Synthetic recovery tests PASS; real production reconciliation BLOCKED_EXTERNAL until the final SSH/runtime stage.**

No production volume was read, moved, migrated, recalculated or overwritten. Repository source custody must not be confused with the untracked `project_output*` estate. The source artifact for bd65a3 was compared locally: 720 regular files matched before the three documented follow-up changes; later commits require their own source comparison.

## Implemented safeguards

`tools/recovery_snapshot.py` requires the caller to stop writers and refuses an existing/overlapping destination, symlinks and special entries. It compares file sizes/SHA-256 before and after copying, validates the snapshot manifest, then restores into a NEW temporary directory. Byte identity is checked before SQLite integrity/foreign-key checks and per-table row counts on that isolated restored copy. WAL is recovered only in the copy; source data are never opened for database writes.

Eight tests cover exact bytes and decision counts, a committed non-checkpointed SQLite WAL, missing quiescence, altered and unexpected files, overwrite/nesting, symlinks and unsafe manifest paths. They are part of the full local 1,044-test suite. No real scientific payload is used.

The deploy workflow requires a stopped old container, no other running container mounting the named output volume, a read-only mount for the snapshotter and a successful isolated restore proof before promotion. Backups/configuration remain on protected server storage, not in Actions artifacts or public Git. Out-of-container workers and sufficient backup/rehearsal disk space still require actual operational verification; a command-line quiescence assertion alone cannot prove this.

## Acceptance after runtime access

Capture read-only manifests and consistent database snapshots. Reconcile article IDs/aliases, searches/hits, placements/grants, decisions, audit chains and exports independently per project. Check raw hashes, orphan relations, foreign keys, duplicate associations and full-text access rights. Counts not observed remain unknown, not zero. Preserve before/after evidence and unexpected-change exceptions.

UNKNOWN and mixed physical containers remain excluded from ownership activation until evidence permits safe logical decomposition. No automatic historical A1/A2 reassignment, ID rewrite or scientific rollback is authorized. A passing fixture restoration proves the algorithm's tested cases, not recovery of the actual production estate.
