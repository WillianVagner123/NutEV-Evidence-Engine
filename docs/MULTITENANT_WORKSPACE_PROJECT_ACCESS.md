# Nut Evidence Platform — Workspace / Project Access

**PR-3 scope:** authoritative Workspace Service + Project Service + Permission Service integration and basic server-backed context switchers.

This PR does not scope searches yet and does not migrate any historical scientific asset.

## Hierarchy

```text
Authenticated User
  ↓
Principal
  ↓
Workspace membership
  ↓
Project access
  ↓
Permission Service
```

A `workspace_id` or `project_id` received from the browser is only a target identifier. It is never proof of access.

## Platform tenancy schema

The PR extends the existing platform database with access metadata only:

```text
platform_tenancy_meta
platform_workspaces
platform_workspace_memberships
platform_projects
platform_session_contexts
```

No scientific payload, query, screening decision, extraction, full text, PRISMA state or manuscript is stored in these tables.

### `platform_workspaces`

```text
id
name
slug
owner_user_id
created_at
status
```

### `platform_workspace_memberships`

```text
workspace_id
user_id
role
status
invited_by
joined_at
```

### `platform_projects`

```text
id
workspace_id
name
slug
description
project_type
status
created_by
created_at
updated_at
```

### `platform_session_contexts`

```text
session_id
user_id
workspace_id
project_id
updated_at
```

This table stores navigation context only. **Selection is not authorization.** Every later private operation must independently re-authorize the target.

## Workspace Service

`WorkspaceProjectService` exposes a server-side membership loader used by `SessionPrincipalService`. Every session resolution therefore reconstructs the Principal from the current membership state.

Consequences:

- a removed/suspended membership stops authorizing access on the next request;
- the frontend cannot inject memberships into a Principal;
- cross-workspace IDs fail closed;
- the workspace owner membership cannot be disabled through the ordinary status mutation primitive.

`provision_workspace()` is deliberately an explicit bootstrap/migration primitive. PR-3 does not publish a self-service workspace creation endpoint and does not auto-create Willian or any named tenant.

## Project Service

Project-wide access is currently available to:

```text
WORKSPACE_OWNER
WORKSPACE_ADMIN
RESEARCHER
VIEWER
```

The project still applies Permission Service rules to each operation. A Viewer resolving a project context does not gain screening/extraction permissions.

`REVIEWER` and `GUEST_REVIEWER` do **not** receive automatic access to the whole project. Their future assigned-item access belongs to the HumanReviewEngine/assignment boundary.

For every project target:

```text
Principal
  ↓
active workspace membership
  ↓
project exists AND belongs to that workspace
  ↓
role has project-wide access or future assignment scope
  ↓
Permission Service
```

Knowing a valid `project_id` from another workspace is insufficient.

## Context API

Available only in `NUTEV_AUTH_MODE=pilot` with a valid authenticated session:

```text
GET  /api/context
POST /api/context/select
```

`GET /api/context` returns only the workspaces accessible by the current Principal and the projects visible in the selected workspace.

`POST /api/context/select` accepts target IDs but validates them server-side. Unknown, malformed, removed, foreign-workspace and foreign-project targets use the same anti-enumeration response:

```text
404 {"error":"context_not_found"}
```

No context is accepted from a `user_id` parameter.

## Switchers

Basic switchers are loaded on:

```text
/
/search.html
/articles.html
```

They use:

```text
workspace-context.js
```

The script:

- reads context from `/api/context`;
- persists selection only through `/api/context/select`;
- does not write workspace/project IDs to `localStorage` or `sessionStorage`;
- reloads after switching so all components start from the newly server-validated session context;
- explicitly labels the selection as context rather than permission.

If auth is `legacy`, there is no authenticated session, or the user has no workspace, the legacy UI remains unchanged.

## Relationship to search

PR-3 deliberately does **not** change:

```text
POST /api/search/jobs
GET  /api/search/jobs/<job_id>
GET  /api/searches
GET  /api/searches/<search_id>
```

Search remains under the prior browser-session compatibility scope until PR-4. This is intentional to avoid partially claiming multi-tenant search isolation before ownership is written into new search jobs/runs.

PR-4 must consume the server-authoritative context/Principal and persist:

```text
workspace_id
user_id
project_id? 
job_id
search_id
```

without migrating historical searches.

## Backwards compatibility

`NUTEV_AUTH_MODE=legacy` remains the default. Tenancy/auth tables are lazy and do not affect normal legacy startup.

No historical browser-session owner is mapped to a User/Workspace by this PR.

## Security properties tested

- tenant A cannot resolve workspace B;
- tenant A cannot combine workspace A with project B;
- knowing project ID does not bypass workspace membership;
- reviewer cannot open the whole project;
- viewer can resolve read context but cannot gain screening permission;
- removed membership stops authorizing new Principals;
- session Principal reloads memberships on every resolve;
- context persists across refresh by session;
- switching workspace clears the selected project;
- context is cleared when membership disappears;
- context UI is server-backed and uses no browser storage;
- PR-3 does not accidentally scope or mutate search jobs before PR-4.

## Scientific impact

None.

```text
NO search execution
NO search ownership migration
NO Registry mutation
NO Workbench mutation
NO Article 1 mutation
NO Article 2 mutation
NO validation decision mutation
NO PRESS/GF-10 change
NO PRISMA event
```

## Rollback

Revert PR-3. New platform tenancy/context tables may remain unused in the isolated platform database. No scientific data rollback is required because the PR does not mutate scientific state.
