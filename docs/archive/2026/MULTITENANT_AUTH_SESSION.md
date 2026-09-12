# Nut Evidence Platform — Authentication + Session Pilot

**PR-2 scope:** explicit Authentication → Session → Principal for a compatibility-safe pilot surface.

This layer does **not** migrate search history, Article Registry state, Workbench state, Article 1, Article 2, human review decisions, PRISMA events or any scientific output.

## Runtime modes

```text
NUTEV_AUTH_MODE=legacy   # default
NUTEV_AUTH_MODE=pilot
```

### `legacy`

Current production behavior is preserved:

- Caddy Basic Auth remains the outer compatibility perimeter;
- existing browser-session isolation for search/history remains unchanged;
- platform login endpoints return `auth_pilot_disabled`;
- no platform auth database is opened merely by starting the server.

### `pilot`

Enables only:

```text
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/status
GET  /api/auth/me     # protected pilot endpoint
```

Existing search/scientific endpoints are **not** silently converted to authenticated tenancy in this PR.

## Authentication provider

The scientific engine does not know how a password or external identity provider works.

Contract:

```text
AuthProvider
  authenticate(email, password)
  load_subject(user_id)
```

Current adapter:

```text
SQLiteAuthProvider
```

A future external IdP can implement the same contract without changing `Principal`, Permission Service, Registry or the scientific primitives.

## Passwords

Local pilot identities use `argon2-cffi` / Argon2 through the maintained library API.

Rules:

- plaintext password is never stored;
- plaintext password is never returned by API;
- plaintext password is never accepted by the provisioning CLI as a command-line argument;
- provisioning reads the password with `getpass`;
- Argon2 hashes may be transparently rehashed when library parameters evolve;
- there is no browser `localStorage`/`sessionStorage` credential contract.

## Session model

Successful authentication creates:

```text
session_id = opaque ses_<uuid>
session_token = cryptographically random opaque secret
```

Only this is persisted:

```text
SHA-256(session_token)
```

The raw session token exists only in the client cookie and transient server memory while the login response is being produced.

Session state records:

```text
session_id
user_id
token_hash
created_at
expires_at
revoked_at
last_seen_at
```

Expired, revoked, forged or unknown tokens fail closed.

If the underlying user becomes suspended/disabled, an otherwise valid session stops producing a Principal and is revoked.

## Cookie

Authenticated session cookie:

```text
nutev_auth_session
Path=/
HttpOnly
SameSite=Lax
Secure              # production / HTTPS
Max-Age=<session ttl>
```

Default TTL:

```text
28800 seconds (8 hours)
```

Allowed range is 60 seconds to 30 days. Invalid runtime configuration fails startup in pilot mode.

The auth cookie is intentionally separate from the existing anonymous:

```text
nutev_session
```

used by the legacy public search/history isolation. PR-2 does not reinterpret old browser-session ownership as a platform user.

## Principal resolution

The authenticated session resolves server-side to a `Principal`.

In PR-2:

```text
user_id
global_roles
session_id
workspace_memberships = ()
```

Workspace memberships remain empty until the authoritative Workspace/Project Service is introduced in PR-3. They are never accepted from a frontend payload.

The `/api/auth/me` response deliberately does **not** expose:

```text
password
password_hash
session_token
session_id
```

It exposes safe identity/profile information and future server-derived membership summaries only.

## Platform admin boundary

A provisioned identity may receive:

```text
PLATFORM_ADMIN
```

This is still governed by the PR-1 contract: it grants platform infrastructure authority only and does **not** bypass workspace/project scientific authorization.

## Explicit provisioning

PR-2 does not auto-create Willian or any other account.

An operator may explicitly provision a pilot identity:

```bash
python tools/provision_nutev_user.py \
  --email researcher@example.org \
  --display-name "Researcher"
```

For infrastructure administration only:

```bash
python tools/provision_nutev_user.py \
  --email admin@example.org \
  --display-name "Infra Admin" \
  --platform-admin
```

The command prompts twice for the password. Never put a password in shell history, environment examples, GitHub, logs or a chat message.

In the Hetzner container the default database is the persistent volume path equivalent of:

```text
/app/project_output_reference/platform/auth.sqlite3
```

No existing scientific database is merged into this auth database.

## Compatibility perimeter

Caddy Basic Auth is preserved during this migration. It is an outer temporary barrier, not a replacement for platform identity.

The target remains:

```text
Authentication
→ Session
→ Principal
→ Authorization
```

`localhost == administrator` remains only a legacy operational compatibility mechanism for older scientific coordinator endpoints. PR-2 does not expand it and does not treat it as authenticated platform identity.

## Security tests required by this PR

- bad credentials → 401 with generic response;
- no session → protected pilot endpoint 401;
- forged session → 401;
- expired session → deny;
- revoked session → deny;
- suspended user → session invalidated;
- raw session token absent from SQLite;
- password absent from SQLite except Argon2 hash;
- login response contains no session secret;
- production cookie is `HttpOnly`, `Secure`, `SameSite=Lax`;
- logout revokes server session and clears cookie;
- default runtime remains `legacy`.

## What remains for later PRs

```text
PR-3 authoritative Workspace/Project access services and switchers
PR-4 bind search jobs/runs to workspace + optional project
PR-5 Evidence Library / private placements
PR-7 historical ownership migration
PR-8 guest-review session engine
PR-12 full tenant adversarial death test
```

No `NUTEV_AUTH_MODE=enforced` exists in this PR. Introducing broad endpoint enforcement before Workspace/Project access is authoritative would create a false sense of tenant security, so unknown modes fail startup instead.
