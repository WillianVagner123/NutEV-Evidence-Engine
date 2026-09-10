# Production smoke report

2026-09-10. **BLOCKED_EXTERNAL / NOT VERIFIED**.

Latest observed main deployment: run 34275710592, attempt 3, job 102252237328, baseline SHA 0c354e23150f74692cd623007c5acc27a93fe28b. Configure SSH failed on 2026-09-08T21:54:05Z because the configured key was not parseable as the expected unencrypted private key after normalization. Verify SSH and Deploy were skipped. This run did not connect or update production.

Owner action: correct HETZNER_SSH_KEY in the repository's HETZNER environment using the complete matching private key through the secrets UI. Do not paste it in chat, source, PR comments, artifacts or logs. Verify its public half matches authorized access on the intended host. Do not weaken the key parser or authentication gate to force success.

The audit environment could not resolve/retrieve the public endpoint; no valid HTTP response was obtained. That is an observation limitation, NOT proof of service outage. Current production commit, NUTEV_AUTH_MODE, provider availability, authenticated tenant routes and real volume contents remain unobserved.

After reviewed candidate checks and configuration correction: validate host identity and SSH access; prove backup/recovery readiness; build/promote only the exact verified SHA; run local container contract and privacy checks; confirm pilot mode; verify HTTPS edge and `/api/version.commit`; perform controlled non-destructive two-project smoke. Basic Auth 401 at the edge alone does not prove internal tenant security or version identity.

A2 may remain dark-launched/404 according to its documented contract; enabling it must not bypass binding. A1 remains private. No scientific search, provider query, ownership activation or production migration is a smoke-test side effect authorized by this report.
