# Production SMTP Runbook

The NutEV password-reset endpoint deliberately returns a generic HTTP 202 even when
mail delivery is unavailable. Production therefore treats SMTP delivery readiness as
an operator concern that must be proven separately from the public reset API.

## GitHub Environment: HETZNER

Configure these **environment variables**:

- `NUTEV_SMTP_HOST`
- `NUTEV_SMTP_PORT` — normally `587`
- `NUTEV_SMTP_USERNAME` — leave empty only for an unauthenticated trusted relay
- `NUTEV_SMTP_FROM`
- `NUTEV_SMTP_STARTTLS` — normally `true`

Configure this **environment secret**:

- `NUTEV_SMTP_PASSWORD`

Do not put the SMTP password in repository files, workflow-dispatch inputs, issue
comments, chat messages, or artifacts.

The existing HETZNER deployment variables/secrets are also required:
`HETZNER_HOST`, `HETZNER_USER`, `HETZNER_PORT`,
`HETZNER_KNOWN_HOSTS`, `HETZNER_APP_DIR`, `NUTEV_PUBLIC_URL`, and
`HETZNER_SSH_KEY`.

## Workflow

Run **configure-production-smtp** from `main`.

### inspect

Read-only. It reports only safe markers:

- production commit;
- effective public origin;
- whether mail delivery is configured;
- whether an SMTP TLS/auth/NOOP probe succeeds;
- whether password-reset delivery is operationally ready.

It never prints the SMTP password.

### apply

The workflow:

1. validates the HETZNER environment settings before mutation;
2. transfers the SMTP settings over the already-pinned SSH connection in a mode-600
   temporary file;
3. backs up the current production `.env`;
4. atomically changes only `NUTEV_SMTP_*`;
5. recreates only the `nutev` container with the existing image;
6. verifies health and proves the production Git SHA is unchanged;
7. proves SMTP TLS/auth/connectivity with a live NOOP;
8. proves the public reset origin still equals `NUTEV_PUBLIC_URL`;
9. optionally issues a real one-time password-reset token for the existing bootstrap
   PLATFORM_ADMIN and sends it using the canonical password-reset store and mailer;
10. removes temporary secret-bearing files.

Any failure after mutation restores the previous `.env` and recreates the app from
that configuration. The workflow does not modify workspace/project permissions or
scientific state.

## Successful closeout markers

A fully configured runtime must show:

```text
EMAIL_DELIVERY_CONFIGURED
SMTP_CONNECTIVITY_READY=true
PASSWORD_RESET_DELIVERY_READY=true
PUBLIC_ORIGIN_EFFECTIVE=https://nutev.mindsperformance.com.br
PRODUCTION_SHA_PRESERVED=<current main SHA>
```

When the optional real reset is requested, the workflow must additionally show:

```text
BOOTSTRAP_PASSWORD_RESET_DELIVERY=sent
```

The raw reset token is never printed.
