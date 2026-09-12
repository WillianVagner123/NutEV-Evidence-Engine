# NutEV — Tenant Search Isolation Contract

Status: **current v1.1.0 hosted-product contract**.

## Ownership rule

Every new authenticated search is bound to tenant ownership before its worker starts.

Private ownership metadata records:

```text
workspace_id
user_id
project_id?   # nullable for workspace-level searches
job_id
search_id?    # bound after the canonical run is persisted
```

This metadata is separate from the global bibliographic Registry. Bibliographic identity may be global; query/job/history context is private.

## Fail-closed execution

In hosted `NUTEV_AUTH_MODE=pilot` mode, creating a search requires:

```text
valid session
→ Principal
→ selected active workspace
→ optional authorized project
→ search-run permission
→ tenant ownership persisted
→ only then background worker starts
```

If ownership persistence fails, the worker is not allowed to continue as an unowned tenant search.

When the run completes, `job_id → search_id` is bound server-side. A persisted result whose tenant ownership cannot be established is preserved but not exposed through authenticated tenant history.

## Job and history access

Exact foreign IDs do not bypass authorization.

```text
GET /api/search/jobs/<job_id>
GET /api/searches?scope=workspace
GET /api/searches?scope=project
GET /api/searches/<search_id>
```

The server revalidates current session, workspace/project context and permission. Foreign, unknown and historical-unowned resources use non-enumerating not-found behavior.

Workspace history is limited to searches explicitly owned by the selected workspace. Project history is limited to the selected project. Switching workspace/project changes the visible set immediately; stale browser context does not keep old tenant history visible.

## Historical searches

Historical ownership is never inferred from:

```text
query text
browser/session hashes
folder names
Article 1 / Article 2 labels
the currently logged-in user
```

Unowned historical runs remain unowned until a separate reviewed provenance/migration process establishes their custody. Login or project selection does not silently adopt them.

## Browser contract

The search/history UI obtains tenant context from authenticated server state. It does not make local browser workspace/project IDs authoritative.

Opening a historical result does not silently rerun its query.

## Compatibility boundary

The code retains legacy browser-session isolation for compatibility/recovery. The accepted hosted production baseline is `NUTEV_AUTH_MODE=pilot`, where workspace/project tenant isolation is the authoritative contract.

## Security invariants

The release/death-test contract covers at least:

- exact foreign `job_id` denied;
- exact foreign `search_id` denied;
- foreign searches absent from workspace/project history;
- workspace-level searches excluded from project-only history;
- context switch removes the previous tenant's visible history;
- Viewer may read allowed history but cannot run searches without permission;
- Reviewer/guest do not receive whole-project search history merely from an assignment;
- historical unowned runs are not auto-adopted.

## Scientific boundary

Search isolation changes **who owns and may retrieve a run**, not what the scientific search primitive means. It does not change provider semantics, ranking/deduplication, Registry identity, screening/extraction decisions, Article 1/Article 2 gates, PRESS/GF-10 or PRISMA by itself.
