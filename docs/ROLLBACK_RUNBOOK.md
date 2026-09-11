# Rollback runbook

2026-09-10 (America/Sao_Paulo). **Snapshot/restore algorithm tested on synthetic data; real Docker/production rollback remains to be rehearsed at the final SSH stage.**

## Implemented release sequence

The updated deploy preserves the previous deploy directory/configuration outside Git on protected storage before checkout. It records the old immutable image ID, deployed SHA, Compose project and output volume. Candidate preflight runs without the production volume.

Before promotion, stop the old application and verify no other running container mounts the output volume. All additional host workers must be stopped by the operator too. Snapshot the output through a read-only mount with `tools/recovery_snapshot.py --quiesced`. The tool refuses unsafe/overlapping paths, verifies byte hashes against an unchanged source, validates its manifest, restores into an isolated temporary directory and runs SQLite integrity/FK/count checks including WAL data. Promotion requires the resulting restore proof.

For an error before promotion after stopping the old container, the error trap restarts the old container. For an error after promotion, rollback uses the recorded immutable prior image and the saved Compose/env configuration with the original project name. It checks both health and the exact old SHA. Failed rollback verification is an explicit manual-recovery error; success never turns the failed release green. Automatic rollback does not overwrite scientific data.

## Evidence and limits

Eight synthetic snapshot tests pass, including a committed non-checkpointed SQLite WAL and rejected tampering. Four static workflow tests pin ordering, read-only source mounting, saved configuration use, exact old-version verification and trusted host checking. These tests are not execution of Docker on the actual server.

At final readiness, prove source volume identity, all writers quiesced, capacity for snapshot plus temporary restored copy, retained old image/configuration, backup permissions and schema compatibility. Initial installation without a previous container intentionally fails and needs a separate reviewed procedure. Unexpected filesystem entries or inconsistent snapshots block, rather than silently omit data.

## Manual data recovery

Restore into a NEW isolated volume first, verify hashes/counts/audit chains and ownership, and preserve any post-snapshot human decisions. Never overwrite the live volume or downgrade an incompatible schema automatically. A successful image rollback is not evidence that a data migration was reversed. Historical ownership binding remains separate and requires reviewed provenance. Keep all secret env files, private manifests and backups out of public Git/Actions artifacts.

No real production backup, rollback or data restoration was performed by this closeout execution.
