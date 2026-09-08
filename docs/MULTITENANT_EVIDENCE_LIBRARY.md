# Nut Evidence Platform — Global Evidence Registry + Private Evidence Library

**PR-5 scope:** preserve one global bibliographic identity and add private tenant placements and full-text access grants around it.

This PR does not migrate historical Workbench state, screening, extraction, Article 1, Article 2, IndexedDB saves or any prior browser-session asset.

## Core invariant

```text
GlobalDocument != Placement != ScientificDecision
```

A global document answers **what bibliographic object is this?**

A placement answers **how does this workspace/project currently use this document?**

A later scientific workflow answers **what decisions/extractions/reviews were made in that project?**

These layers are intentionally separate.

## Global Evidence Registry

The canonical Article Registry remains the single bibliographic identity authority.

PR-5 does not create a second DOI/PMID/title deduplicator or a second `article_id`.

The read-only `GlobalEvidenceRegistryReader` projects only globally shareable bibliographic fields:

```text
article_id
title
year
journal
public abstract
DOI
PMID
PMCID
```

It does not expose:

```text
screening decision
project note
tags
extraction
reviewer judgment
PRISMA state
full-text bytes
storage_path
cache_path
workspace ownership
project ownership
```

## Placement

Private relation:

```text
Workspace / Project
       ↓
    Placement
       ↓
 GlobalDocument(article_id)
```

Schema:

```text
platform_document_placements
```

Fields:

```text
placement_id
workspace_id
project_id?     # NULL = workspace-level library placement
article_id      # canonical global Registry identity
state
tags_json
notes
created_by
created_at
updated_at
```

Allowed placement states in PR-5:

```text
not_screened
included
excluded
background
```

These values are **private placement state**, not global article attributes and not automatically PRISMA events.

The same `article_id` can therefore be:

```text
Workspace A / Project A → included + A notes
Workspace B / Project B → background + B notes
```

without either tenant seeing or mutating the other state.

## Placement deletion

Deleting a Placement:

```text
DELETE private relation
```

It must never:

```text
delete GlobalDocument
delete article aliases
delete Registry manifestations
delete another workspace Placement
delete another project Placement
```

## Workspace and project scopes

### Workspace scope

A workspace-level library view may include all Placements belonging to that workspace, including project-bound Placements, for roles authorized to read the workspace Evidence Library.

A workspace-level saved Placement uses:

```text
project_id = NULL
```

### Project scope

A project view contains only:

```text
workspace_id = current workspace
AND project_id = current project
```

Selecting a project does not grant access. `WorkspaceProjectService` and the Permission Service re-authorize every operation.

## Permissions

PR-5 adds explicit permissions:

```text
EVIDENCE_LIBRARY_READ
EVIDENCE_LIBRARY_WRITE
FULL_TEXT_ACCESS_READ
FULL_TEXT_ACCESS_MANAGE
```

### OWNER / ADMIN / RESEARCHER

May read/write the Evidence Library and read/manage full-text access grants in authorized contexts.

### VIEWER

May read the Evidence Library and active full-text access descriptors, but may not create/update/delete Placements.

### REVIEWER / GUEST_REVIEWER

Do not receive the whole Evidence Library merely because they can later receive assigned review items. Assignment-scoped scientific access remains the HumanReviewEngine boundary.

## FullTextAccessGrant

Full text is not made globally readable merely because an artifact exists.

Private grant schema:

```text
platform_full_text_access_grants
```

Fields:

```text
grant_id
workspace_id
project_id?
article_id
artifact_id?
provider_record_id
access_type
license_text
access_url
cache_path                 # server-internal only
redistribution_allowed
expires_at
created_by
created_at
updated_at
```

A grant may expire. Expired grants are not returned as active access.

A workspace-level grant may apply within its workspace; a project-level grant is restricted to its project context.

## Browser-safe full-text API

```text
GET /api/library/full-text/<article_id>
```

returns only safe descriptors such as:

```text
access_type
license
access_url
redistribution_allowed
expires_at
artifact_id/provider record identifiers when present
```

It does **not** return:

```text
cache_path
storage_path
filesystem location
full-text bytes
```

The HTTP API intentionally has no endpoint that accepts arbitrary browser-provided `cache_path` to create a grant. Grant management remains a trusted server/service operation in PR-5.

## Authenticated Evidence Library API

Available only through the authenticated pilot boundary:

```text
GET    /api/library?scope=workspace|project
GET    /api/library/placements/<placement_id>
POST   /api/library/placements
DELETE /api/library/placements/<placement_id>
GET    /api/library/full-text/<article_id>
```

Foreign placement IDs return the same external behavior as unknown IDs:

```text
404 placement_not_found
```

The API never accepts a frontend `user_id` to determine ownership.

## Pilot UI

A dedicated transitional page is provided at:

```text
/evidence-library.html
```

It:

- uses server-authenticated workspace/project context;
- lists server-side Placements;
- saves only a canonical `article_id` that already exists in the Registry;
- keeps tags/notes/state private;
- can inspect safe full-text grant descriptors;
- does not use browser storage for tenant identity;
- does not expose cache paths.

The page is intentionally explicit about the distinction between bibliographic metadata and private scientific state.

## Existing IndexedDB Saved Library

The pre-multi-tenant product contains a browser-local saved-library implementation in IndexedDB.

PR-5 does **not** reinterpret those records as platform ownership.

Rules:

```text
legacy runtime → existing local Saved Library remains compatible
pilot tenant state → server Evidence Library is authoritative
historical IndexedDB items → no automatic migration
```

A compatibility facade is prepared for later UI cutover, but no local item is silently uploaded or assigned to a Workspace/Project.

## Why no automatic local migration

An IndexedDB record proves only that a browser stored an item. It does not prove:

```text
which authenticated user owns it
which workspace owns it
which project owns it
whether it belongs to A1/A2
whether notes are redistributable
```

Therefore automatic adoption would violate the migration invariant against inferred ownership.

## Security death tests

PR-5 tests:

```text
same article_id in Tenant A and B
→ same GlobalDocument identity
→ different Placement IDs
→ different state/tags/notes

Tenant B knows A placement_id
→ 404 / no access

A updates Placement
→ B unchanged
→ GlobalDocument unchanged

A deletes Placement
→ B Placement remains
→ GlobalDocument remains

A full-text grant
→ B receives no grant

expired grant
→ not active

safe API payload
→ no cache_path/storage_path

Viewer
→ read allowed
→ write denied

Reviewer
→ whole library denied
```

## Scientific impact

None to retrieval/ranking/adjudication semantics.

```text
NO provider change
NO query change
NO ranking change
NO deduplication change
NO Article Registry identity rewrite
NO screening execution
NO extraction execution
NO human decision mutation
NO A1 mutation
NO A2 mutation
NO PRESS/GF-10 change
NO PRISMA event
```

Placement state is not promoted to a global scientific conclusion.

## Migration impact

None.

This PR does not:

```text
migrate Workbench
migrate Article 1
migrate Article 2
migrate saved IndexedDB records
migrate browser-session search ownership
copy full text between tenants
infer redistribution rights
```

Historical placement migration must be explicit and hash-audited in the later Willian/A1/A2 migration PR.

## Rollback

1. keep/return runtime to `NUTEV_AUTH_MODE=legacy` if operational rollback is needed;
2. revert PR-5;
3. leave the private placement/grant tables unused in the platform DB;
4. the canonical Article Registry remains unchanged;
5. no scientific artifact requires recomputation or rerun.

## Next gate

After PR-5 is green and merged, PR-6 introduces `ResearchApplication` and versioned application templates. Applications may reference the same Engine primitives and Placements but must not duplicate the Engine or convert private state into global metadata.
