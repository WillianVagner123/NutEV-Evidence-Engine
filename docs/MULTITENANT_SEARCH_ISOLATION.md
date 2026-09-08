# Nut Evidence Platform — Tenant Search Isolation

**PR-4 scope:** bind every **new authenticated search** to workspace ownership before the background worker starts, and enforce the same scope on job polling and persisted history.

This PR does **not** migrate historical searches. Legacy runs without an explicit row in the new ownership store remain preserved on disk and invisible to authenticated tenant history until the dedicated migration PR.

## Ownership contract

Every new authenticated search job records:

```text
workspace_id
user_id
project_id?   # nullable for workspace-level searches
job_id
search_id?    # bound only after the job persists a completed run
```

The private platform table is:

```text
platform_search_ownership
```

with:

```text
job_id PRIMARY KEY
search_id UNIQUE NULLABLE
workspace_id
user_id
project_id NULLABLE
created_at
search_bound_at
```

This metadata is separate from the Global Evidence Registry. Bibliographic `article_id` remains global; the query/job/history context is private.

## Fail-closed job creation

In `NUTEV_AUTH_MODE=pilot`:

```text
POST /api/search/jobs
```

requires:

```text
valid authenticated session
→ Principal
→ selected workspace context
→ active workspace membership
→ optional project access
→ Permission.SEARCH_RUN
```

The sequence is deliberately:

```text
validate query/context
→ register in-memory job
→ persist tenant ownership
→ start background worker
```

If ownership persistence fails, the worker thread is not started and the in-memory job is removed.

This prevents a search from running first and only later discovering that its owner could not be recorded.

## Search completion

The worker still uses the existing scientific/search implementation and persists the canonical result as before.

A separate server-side watcher binds:

```text
job_id → search_id
```

only after the canonical run exists.

If that bind fails, the result remains preserved but is **not exposed in authenticated history**. The system fails closed instead of guessing ownership.

## Job access

```text
GET /api/search/jobs/<job_id>
```

In pilot mode:

1. resolves the authenticated Principal;
2. loads current server-side workspace context;
3. finds the private ownership record;
4. requires the current workspace to equal the owner workspace;
5. revalidates membership/project access;
6. requires search-history permission;
7. otherwise returns `404 search_job_not_found`.

Knowing another tenant's exact `job_id` is insufficient.

## Persisted history

Authenticated history supports:

```text
GET /api/searches?scope=workspace
GET /api/searches?scope=project
```

### Workspace scope

Returns only searches explicitly owned by the current selected workspace.

It includes:

- workspace-level searches (`project_id = NULL`);
- project searches belonging to that workspace.

### Project scope

Requires a selected project and returns only searches with exactly that `project_id`.

### Read permission

PR-4 introduces:

```text
Permission.SEARCH_HISTORY_READ
```

Granted to:

```text
WORKSPACE_OWNER
WORKSPACE_ADMIN
RESEARCHER
VIEWER
```

Not granted to:

```text
REVIEWER
GUEST_REVIEWER
```

Reviewer access remains assignment-scoped through the future HumanReviewEngine; a reviewer does not gain the complete query/history corpus of a project merely by being assigned scientific review items.

## Persisted run readers

`list_search_runs()` and `load_search_run()` now accept:

```text
allowed_search_ids
```

Semantics:

```text
None        = legacy/internal caller did not request this guard
empty set   = return/load nothing
nonempty    = only those pre-authorized IDs
```

This is a defense-in-depth boundary in addition to HTTP authorization.

## Direct search access

```text
GET /api/searches/<search_id>
```

In pilot mode requires an ownership record and current workspace access. Unknown, historical-unowned and foreign-tenant IDs all resolve to the same external behavior:

```text
404 search_not_found
```

The API does not reveal whether a foreign ID exists.

## Current context versus ownership

Workspace switching is significant:

```text
current workspace A → search A visible
switch to workspace B → search A no longer visible
```

A user who legitimately belongs to both workspaces must switch back to A before accessing A history. This prevents stale-context leakage after workspace switching.

Project switching affects the `scope=project` subset. Workspace scope may show all searches owned by that workspace to roles authorized to read workspace search history.

## Search UI

`search-history-ui.js` exposes:

```text
Buscas do workspace
Buscas do projeto
```

The selector calls the scoped backend endpoint. It does not persist tenant IDs in `localStorage` or `sessionStorage`.

The existing behavior “use the question to prepare a new search” remains unchanged; opening history never silently reruns the old search.

## Legacy compatibility

Default remains:

```text
NUTEV_AUTH_MODE=legacy
```

Legacy mode preserves:

- anonymous `nutev_session` browser cookie;
- `_JOB_OWNERS` in-memory job isolation;
- `.ownership.json` persisted search mapping;
- legacy `/api/searches` browser-session history;
- the existing background ownership watcher.

These mechanisms are compatibility paths only. They do not become platform Workspace ownership.

## Historical runs

PR-4 explicitly forbids:

```text
NO bulk import of .ownership.json into workspace ownership
NO assignment based on query text
NO assignment based on browser hash
NO assignment based on article1/article2 folder names
NO assignment based on current logged-in user
```

Historical ownership waits for the explicit dry-run migration with hashes and manifests.

## Scientific boundary

The search engine itself remains the same scientific primitive. PR-4 changes **who owns and may retrieve a run**, not what the query returns or how articles are normalized/ranked.

```text
NO provider change
NO ranking change
NO deduplication change
NO Registry identity change
NO Workbench change
NO screening/extraction change
NO A1/A2 mutation
NO PRESS/GF-10 change
NO PRISMA event
```

## Death tests

Required and implemented:

```text
Tenant A runs search A
Tenant B knows A job_id       → 404
Tenant B knows A search_id    → 404
Tenant B workspace history    → no A
Tenant A project history      → A only when project-scoped
workspace-only search         → excluded from project history
A switches workspace          → old workspace search disappears
historical unowned run        → not adopted automatically
viewer                        → history read allowed, search run denied
reviewer                      → whole history denied
```

## Rollback

1. set/keep `NUTEV_AUTH_MODE=legacy` if operational rollback is needed;
2. revert PR-4;
3. leave `platform_search_ownership` unused in the isolated platform DB;
4. canonical persisted search results and the Global Evidence Registry remain intact;
5. no scientific-data rollback or search rerun is required.

## Next gate

After PR-4 is fully green, PR-5 may implement the Evidence Library / Global Registry `Placement` boundary. It must not infer private project state from global article identity.
