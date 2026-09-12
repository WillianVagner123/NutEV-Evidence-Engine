# NutEV — Multi-tenant Authentication and Session Contract

Status: **current v1.1.0 hosted-product contract**.

The original PR-2 implementation note is preserved at [`archive/2026/MULTITENANT_AUTH_SESSION.md`](archive/2026/MULTITENANT_AUTH_SESSION.md). This document describes the supported state of the current product rather than the migration sequence that created it.

## Runtime modes

The server accepts two compatibility modes:

```text
NUTEV_AUTH_MODE=legacy
NUTEV_AUTH_MODE=pilot
```

The code-level fallback remains `legacy` when the variable is omitted, so accidental configuration changes fail predictably against the compatibility behavior. **The accepted hosted production baseline for v1.1.0 is `NUTEV_AUTH_MODE=pilot`.** The production release gate verifies that mode explicitly.

`legacy` exists for compatibility/recovery work. It is not the tenant-security baseline used to describe the hosted product.

## Authentication boundary

In `pilot` mode identity is established server-side through the platform authentication/session layer. The browser does not select its own user, workspace, project or application identity by supplying IDs as proof of ownership.

Core auth endpoints include:

```text
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/status
GET  /api/auth/me
```

Authenticated product operations resolve a server-side `Principal` and then apply workspace/project/application authorization. Knowing an opaque resource ID or URL is not sufficient authorization.

## Password and session storage

Local provisioned identities use Argon2 password hashes. Plaintext passwords are not persisted and the provisioning CLI reads passwords interactively rather than accepting them as a command-line argument.

A successful login creates an opaque session token. Persistent session state stores the token's SHA-256 digest rather than the raw token. Expired, revoked, forged or unknown sessions fail closed.

The authenticated browser session uses the `nutev_auth_session` cookie. Production/HTTPS behavior requires the security attributes enforced by the server contract, including `HttpOnly`, `Secure` and `SameSite=Lax`.

## Tenant authorization

Authentication and authorization are separate gates:

```text
Authentication
→ Session
→ Principal
→ Workspace membership
→ Project access
→ ResearchApplication / resource-specific authorization
```

Workspace membership and project access are server-authoritative. Client-supplied ownership claims do not replace those checks.

`PLATFORM_ADMIN` is infrastructure authority and is not an implicit bypass into private scientific state. Scientific/private project access still requires the authorized tenant path or another explicit narrowly scoped mechanism defined by the relevant service.

## Provisioning

There is no promise of public self-registration in v1.1.0. Accounts are provisioned explicitly with the maintained operator tooling, including `tools/provision_nutev_user.py`.

The hosted product's tenant/auth databases live on persistent production storage; they are not merged into the bibliographic Registry or treated as scientific evidence.

## Outer proxy perimeter

The Hetzner deployment may retain host/proxy controls such as Caddy for transport/routing and an outer compatibility perimeter. Those controls do not replace application identity, tenant scoping or project authorization.

## Security invariants

The current contract requires, at minimum:

- invalid credentials or invalid sessions fail closed;
- raw passwords and raw session tokens are not persisted;
- logout revokes the server-side session;
- disabled/suspended users cannot keep using an otherwise valid session;
- tenant/project scope is derived server-side;
- cross-workspace and cross-project access is denied;
- infrastructure-admin status alone does not grant private scientific read access;
- production promotion uses the multi-tenant release/death-test gates rather than relying on documentation assertions.

See also:

- [`MULTITENANT_WORKSPACE_PROJECT_ACCESS.md`](MULTITENANT_WORKSPACE_PROJECT_ACCESS.md)
- [`MULTITENANT_APPLICATION_LAYER.md`](MULTITENANT_APPLICATION_LAYER.md)
- [`FINAL_MULTITENANT_RELEASE_GATE.md`](FINAL_MULTITENANT_RELEASE_GATE.md)
- [`AUDITABILITY_AND_GUARDRAILS.md`](AUDITABILITY_AND_GUARDRAILS.md)
