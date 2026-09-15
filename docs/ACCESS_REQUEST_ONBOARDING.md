# NutEV — Governed Access Request and Account Onboarding

Status: **hosted-product access flow**.

## Goal

NutEV does not use open self-registration. A person may request access from the public login surface, but an account is created only after a platform administrator approves the request and the invited person sets their own password.

This flow is part of platform identity management. It does **not** create scientific state, infer eligibility, grant project access, or change review/evidence decisions.

## User flow

```text
/login.html
  -> /access-request.html
  -> POST /api/access-requests
  -> pending administrative review

PLATFORM_ADMIN
  -> /access-admin.html
  -> GET /api/admin/access-requests
  -> approve or reject

approve
  -> one-time invitation token
  -> /set-password.html?token=...
  -> invited person defines password
  -> POST /api/access-invitations/accept
  -> account created
  -> /login.html
  -> existing first-login/onboarding flow
```

## Public request fields

The request collects only:

- full name;
- email;
- institution / organization;
- intended scientific use.

The UI explicitly asks people not to place passwords, identifiable clinical data, or other sensitive information in the free-text purpose field.

Public submission responses are deliberately generic. The endpoint does not disclose whether the email already has an account or an open request.

Open requests are deduplicated case-insensitively by email. A later request may be submitted after an earlier request is rejected.

## Administrative decision

Only a server-resolved principal with `PLATFORM_ADMIN` may list or decide access requests.

Approval does **not** create a user immediately. It issues a temporary invitation. Re-approving an already approved request rotates the invitation and invalidates the previous link.

Rejection clears any active invitation token hash.

The administration screen exposes the generated invitation link only when it is issued or rotated. The operator can copy it and send it through an appropriate communication channel. NutEV does not claim that email delivery exists when no email provider is configured.

## Invitation security

Invitation tokens:

- are generated with cryptographically secure randomness;
- expire after 72 hours by default;
- are single-use;
- are never stored in raw form;
- are persisted only as a SHA-256 digest;
- are removed from the browser URL with `history.replaceState` after the password page reads them;
- use a `no-referrer` password-setup page;
- are invalid after account creation or rejection.

The password itself is submitted only by the invited person. Account provisioning reuses the canonical `SQLiteAuthProvider`, which applies the existing password policy and Argon2 hashing.

If the invitation changes during account creation, the newly provisioned account is disabled rather than left active outside the governed request state.

## Authorization boundary after account creation

A new account has no implicit global role, workspace membership, project access, or research application.

```text
approved access request
  != PLATFORM_ADMIN
  != workspace membership
  != project authorization
  != private scientific-data access
```

Workspace/project onboarding remains a separate server-authoritative step.

## HTTP endpoints

Public / invitation flow:

```text
POST /api/access-requests
GET  /api/access-invitations/status?token=...
POST /api/access-invitations/accept
```

Platform administration:

```text
GET  /api/admin/access-requests?status=pending|approved|accepted|rejected|all
POST /api/admin/access-requests/<request_id>/approve
POST /api/admin/access-requests/<request_id>/reject
```

The admin endpoints perform their own `PLATFORM_ADMIN` authorization and do not rely on client-supplied workspace/project state.

## Anti-abuse and privacy

- Public access requests are rate limited per source IP.
- Invitation acceptance attempts are rate limited per source IP.
- A honeypot field silently absorbs basic automated form submissions.
- Same-origin JSON write enforcement remains active in the secure HTTP boundary.
- Request data is never treated as scientific evidence.
- Request/invitation pages are `noindex,nofollow`.

## Hosted proxy note

The application-authenticated production runtime may sit behind an external reverse proxy. The repository also retains a managed Caddy configuration as a compatibility/recovery perimeter. Proxy controls do not replace application identity or the `PLATFORM_ADMIN` checks described above.
