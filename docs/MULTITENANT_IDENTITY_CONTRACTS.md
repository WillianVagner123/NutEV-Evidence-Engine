# Nut Evidence Platform — Identity and Authorization Contracts

**Status:** PR-1 contract layer. No login/session middleware or production endpoint is wired to this module yet.

This document describes the first reusable multi-tenant contracts introduced after the PR-0 inventory. The purpose is to define identity and authorization semantics before changing search ownership, historical data, Workbench state, Article 1, Article 2 or production storage.

## Principles

```text
User
  ↓
Workspace
  ↓
Project
  ↓
ResearchApplication
```

- IDs are opaque and prefixed (`usr_`, `wsp_`, `prj_`, `app_`, `ses_`).
- `Principal` is server-derived identity context. Private endpoints must never infer identity from a frontend-supplied user id.
- Authorization is fail-closed.
- Workspace membership and project access are distinct checks.
- `PLATFORM_ADMIN` manages platform infrastructure; it is **not** an implicit reader of private scientific state.
- Reviewer access is assignment-scoped.
- Policy-dependent permissions are denied unless the caller supplies an explicit policy grant.
- Role rules live in one Permission Service matrix instead of endpoint-local `if role == ...` branches.

## Contracts

Implemented under:

```text
src/nutev/tenancy/
  models.py
  permissions.py
```

### Identity models

```text
User
Workspace
Membership
Project
ResearchApplication
Principal
```

The models are immutable dataclasses used as domain contracts. This PR does **not** add a database or migrate historical records.

### Principal

A user Principal contains at least:

```text
user_id
workspace_memberships
global_roles
session_id
```

A membership must belong to the same user as the Principal. Duplicate workspace memberships are rejected so authorization cannot resolve an ambiguous role.

### Roles

```text
PLATFORM_ADMIN
WORKSPACE_OWNER
WORKSPACE_ADMIN
RESEARCHER
REVIEWER
VIEWER
GUEST_REVIEWER
```

The guest-reviewer role is defined in the permission matrix for future HumanReviewEngine integration. PR-1 does not define the guest-session/token identity mechanism and therefore does not imply that a guest must possess a normal NutEV user account.

## Permission matrix

The minimum contract is centralized in `ROLE_PERMISSIONS`.

| Permission | Owner | Admin | Researcher | Reviewer | Viewer | Guest |
|---|---|---|---|---|---|---|
| Workspace settings | full | full | deny | deny | deny | deny |
| Members | full | full | deny | deny | deny | deny |
| Transfer ownership | full | deny | deny | deny | deny | deny |
| Delete workspace | policy | deny | deny | deny | deny | deny |
| Create project | full | full | policy | deny | deny | deny |
| Run search | full | full | full | deny | deny | deny |
| See project bank | full | full | full | assigned | full | deny |
| Screen | full | full | full | assigned | deny | assigned |
| Extract | full | full | full | assigned | deny | assigned |
| Adjudicate | full | full | policy | deny | deny | deny |
| Export | full | full | policy | deny | policy | deny |
| Delete project | full | policy | deny | deny | deny | deny |

`policy` means an explicit workspace/project policy grant is required. Absence of that grant is denial.

## Project access handshake

PR-1 does not introduce Project Service persistence yet. For project-scoped permissions, the Permission Service requires:

```text
project_access_confirmed = true
```

This is deliberate. A caller knowing a `project_id` is not enough. PR-3 will provide the Workspace/Project service that resolves membership and establishes this flag after checking the target project belongs to the workspace and the Principal may access it.

If project access has not been independently confirmed, authorization fails closed.

## Assignment scope

For reviewer-style permissions the contract can return:

```text
scope = assigned
```

and requires:

```text
assigned = true
```

before access is granted. The future review engine must derive that flag from backend assignment data, never from a browser parameter.

## Platform admin boundary

`PLATFORM_ADMIN` may receive:

```text
platform.infra.manage
```

It does not grant:

```text
project.bank.read
project.screen
project.extract
project.adjudicate
project.export
```

without a normal authorized workspace/project path or a future explicit support-access grant.

## What PR-1 deliberately does not do

```text
NO login implementation
NO session persistence
NO auth middleware
NO endpoint protection changes
NO Workspace/Project persistence service
NO search ownership changes
NO historical search migration
NO Workbench migration
NO Article 1 migration
NO Article 2 migration
NO guest token implementation
NO production data movement
NO PRISMA/search/scientific-state mutation
```

## Next integration gates

- **PR-2:** Session + Authentication; derive Principal server-side and protect a pilot endpoint with a compatibility flag.
- **PR-3:** Workspace/Project Access services and switchers; establish authoritative project access.
- **PR-4:** bind new search jobs/runs to workspace and optional project ownership.

Until PR-2/PR-3, the existing production handlers keep their current behavior. Merely importing `nutev.tenancy` does not change runtime authorization.
