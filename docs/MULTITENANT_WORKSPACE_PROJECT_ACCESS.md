# NutEV — Workspace / Project Access Contract

Status: **current v1.1.0 hosted-product contract**.

## Authorization hierarchy

```text
Authenticated User
→ Session
→ Principal
→ active Workspace membership
→ Project access
→ Permission Service
→ resource-specific authorization
```

A `workspace_id` or `project_id` supplied by the browser is only a target identifier. It is never proof of access.

## Platform tenancy state

The platform database keeps tenancy/navigation metadata separate from scientific payloads:

```text
platform_tenancy_meta
platform_workspaces
platform_workspace_memberships
platform_projects
platform_session_contexts
```

These tables do not become a second bibliographic registry and do not, by themselves, record screening, extraction, PRISMA, recommendation or manuscript decisions.

`platform_session_contexts` stores the currently selected workspace/project for navigation. **Selection is not authorization**: every private operation revalidates the current membership, project ownership and permission.

## Workspace and project access

`WorkspaceProjectService` is server-authoritative. Session resolution rebuilds the Principal from current membership state, so a removed or suspended membership stops authorizing subsequent requests.

Project-wide access is available only through authorized workspace roles. Reviewer-style access remains assignment-scoped where the Human Review layer grants it; knowing a project ID never grants the whole project.

`PLATFORM_ADMIN` remains infrastructure authority, not an implicit reader of private project/scientific state.

## Context API

In the hosted `NUTEV_AUTH_MODE=pilot` runtime:

```text
GET  /api/context
POST /api/context/select
```

`GET /api/context` returns only workspaces/projects visible to the authenticated Principal.

`POST /api/context/select` validates the requested target server-side. Unknown, malformed, removed or foreign targets use not-found semantics rather than revealing another tenant's resource.

The browser does not persist workspace/project ownership claims in `localStorage` or `sessionStorage`; selection is persisted through the authenticated server session.

## Product navigation

Workspace/project switchers are server-backed. Changing context causes subsequent Search, Library, ResearchApplication, Human Review and Export operations to re-resolve authorization against the newly selected context.

A context switch never migrates or reassigns historical scientific assets.

## Search integration

New authenticated searches are tenant-scoped before execution. Search ownership/history is enforced by the search-isolation contract in [`MULTITENANT_SEARCH_ISOLATION.md`](MULTITENANT_SEARCH_ISOLATION.md).

Historical/unowned runs are not silently adopted because a user selects a workspace/project or happens to be logged in.

## Compatibility boundary

The code retains `legacy` mode for compatibility/recovery. The accepted hosted production baseline for v1.1.0 is `NUTEV_AUTH_MODE=pilot`; see [`FINAL_MULTITENANT_RELEASE_GATE.md`](FINAL_MULTITENANT_RELEASE_GATE.md).

## Security invariants

The current test/release contract requires, among other checks:

- tenant A cannot resolve tenant B's workspace/project using exact IDs;
- a project must belong to the selected authorized workspace;
- removed membership stops authorizing new Principals;
- selection survives refresh only through server session state;
- switching workspace clears/invalidate incompatible project context;
- browser context selection is not treated as permission;
- infrastructure-admin status alone does not bypass private tenant state.

## Scientific boundary

Workspace/project selection and authorization do not execute searches, change providers/ranking, mutate Registry identity, alter screening/extraction/review decisions, activate Article 1/Article 2 scientific gates, or create PRISMA events.
