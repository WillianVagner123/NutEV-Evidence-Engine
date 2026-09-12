# Production smoke report

2026-09-10 (America/Sao_Paulo). **BLOCKED_EXTERNAL / DEFERRED TO FINAL SSH STAGE.**

The user explicitly requested finishing safe adjustments before SSH configuration. No SSH key was changed, no SSH connection or deploy rerun was attempted, and PR #1246 remains separate from main. Tests executed against isolated local/Actions fixtures only.

Last observed main deployment: run 34275710592 attempt 3, job 102252237328, target 0c354e23150f74692cd623007c5acc27a93fe28b. Configure SSH failed because the supplied key could not be parsed. Connection and deployment steps were skipped. That run did not change production. Current production commit/auth mode/volume contents are not inferred from it.

## Final operational setup, not a code workaround

1. Complete code review and final-head checks. Do not merge merely to trigger the old deploy or retry an unchanged failure.
2. Configure the matching private `HETZNER_SSH_KEY` through the HETZNER environment secret settings and a separately verified `HETZNER_KNOWN_HOSTS` entry through trusted settings. No private key in chat/logs/Git; no guessed host key.
3. Inspect readiness and real data owners. Require `NUTEV_AUTH_MODE=pilot`; preserve A2 dark launch/binding gate. Set A1 workspace/project pins only from reviewed ownership evidence; missing pins intentionally deny A1 source access without exposing it to other users.
4. Review all writers, disk capacity and snapshot/restore compatibility. The workflow rejects dirty tracked files, a stale target SHA, absent previous image identity, unsafe snapshot source or failed restore proof.
5. On controlled main promotion, require every workflow for that exact SHA, candidate preflight, quiesced read-only source snapshot and isolated restore proof before replacing the image.
6. Verify live container health, pilot privacy, exact `/api/version.commit`, HTTPS edge and a non-destructive authorized two-project smoke. Basic Auth 401 alone does not prove internal tenant isolation or build identity.
7. Reconcile production manifests/counts and retain protected backup evidence. No scientific search or ownership activation is an implicit smoke-test side effect.

A2 can remain dark-launched with expected 404. A1 academic gates and A2 provenance remain independent. This document does not falsely reduce final acceptance to typing a key: server identity, deployment and real-data verification require actual execution in that final stage.
