# NutEV — Multi-tenant Export & Audit Contract

Status: PR-11 platform boundary.

## 1. Purpose

This layer adds authenticated, tenant-scoped custody for export artifacts that were already produced by an existing NutEV scientific/application primitive.

It does **not** replace or reinterpret `src/nutev/science/export.py`.

```text
scientific/application primitive
        |
        v
already-produced artifact bytes
        |
        v
ProjectExportAuditService
        |
        +--> tenant/project authorization
        +--> SHA-256 each artifact
        +--> private project storage
        +--> tenant export manifest
        +--> append-only hash-chained audit trail
```

The custody layer never infers eligibility, evidence quality, synthesis, certainty, recommendations, PRISMA counts, or manuscript conclusions.

## 2. Authorization

All export/audit operations derive their target from an authenticated `Principal` and an already-confirmed workspace/project context.

The client may not select ownership by sending:

```text
user_id
workspace_id
project_id
application_id
session_id
search_id
owner_scope
```

The active `application_id`, when present, is resolved server-side from `SQLiteApplicationStore` for the selected project.

Permissions:

```text
project.export      -> create/read export content
project.audit.read  -> list exports, inspect manifests, inspect audit events
```

Role defaults:

| Role | export | audit read |
|---|---:|---:|
| WORKSPACE_OWNER | yes | yes |
| WORKSPACE_ADMIN | yes | yes |
| RESEARCHER | explicit policy grant | yes |
| VIEWER | explicit policy grant | yes |
| REVIEWER | no | no |
| GUEST_REVIEWER | no | no |
| PLATFORM_ADMIN without workspace membership | no | no |

`PLATFORM_ADMIN` remains an infrastructure role and is not a private scientific-data bypass.

## 3. Storage boundary

Default artifact root:

```text
project_output_reference/platform/exports/
  <workspace_id>/
    <project_id>/
      <export_id>/
        MANIFEST.json
        <artifact files>
```

The platform database stores only export/audit metadata and artifact hashes. Artifact bodies do not enter the SQLite audit store.

Database tables:

```text
platform_export_audit_meta
platform_project_exports
platform_project_export_artifacts
platform_project_audit_events
```

No Global Registry table, Workbench table, search result, HumanReview table, Article 1 table, or Article 2 table is rewritten by PR-11.

## 4. Export manifest

Every export has a canonical manifest with:

```text
schema_version
export_type
export_id
workspace_id
project_id
application_id
export_kind
created_by
created_at
metadata
artifacts[]
```

Each artifact descriptor contains only:

```text
name
media_type
sha256
size_bytes
```

Internal relative/absolute storage paths are not part of the public artifact descriptor.

The manifest explicitly states:

```text
tenant_scoped = true
project_scoped = true
absolute_storage_paths_exposed = false
scientific_semantics_inferred = false
```

## 5. Artifact security

The platform API accepts only explicit UTF-8 `content_text` for PR-11.

It rejects client-supplied:

```text
filesystem paths
file URLs
remote URLs
base64 source payloads
```

Artifact names are constrained to a safe single filename. Path traversal and subdirectories are rejected.

Allowed media types are intentionally narrow:

```text
application/json
application/x-ndjson
text/csv
text/markdown
text/plain
text/tab-separated-values
```

Before a stored artifact is returned, its current bytes are re-hashed and compared to the recorded SHA-256 and size. A mismatch fails closed.

Responses use `Cache-Control: private, no-store` and `X-Content-Type-Options: nosniff`.

## 6. Audit chain

Every mutating/security-relevant export action creates a private project audit event.

Initial PR-11 event types:

```text
export_created
export_artifact_read
```

Each event records:

```text
event_id
workspace_id
project_id
application_id
actor_user_id
event_type
resource_type
resource_id
details
previous_event_hash
event_hash
created_at
```

`event_hash` is SHA-256 over the canonical event body including `previous_event_hash`.

This makes accidental or malicious modification of an earlier audit event detectable by chain verification. The chain is project-local: one project never anchors to another project's events.

The hash-chain is an integrity control, not a cryptographic signature or external timestamp authority.

## 7. HTTP surface

Pilot-authenticated routes:

```text
POST /api/exports
GET  /api/exports
GET  /api/exports/<export_id>/manifest
GET  /api/exports/<export_id>/artifacts/<name>
GET  /api/audit?limit=<n>
```

`POST /api/exports` example shape:

```json
{
  "export_kind": "SCIENTIFIC_HANDOFF",
  "metadata": {
    "source_sha256": "<sha256>"
  },
  "artifacts": [
    {
      "name": "records.csv",
      "media_type": "text/csv",
      "content_text": "id,value\n1,A\n"
    }
  ]
}
```

There is no endpoint for:

```text
cross-workspace export listing
cross-project export listing
bulk platform export
filesystem path ingestion
historical ownership activation
Article 2 legacy binding
```

## 8. Scientific compatibility

PR-11 does not change:

```text
SEARCH
NORMALIZE
DEDUPLICATE
RANK
science/export.py semantics
Global Registry identity
Article 1 D-132 state
Article 2 LEGACY_BINDING block
HumanReview decisions
PRISMA state
PRESS/GF-10/freeze gates
```

A successful project export means only:

> the supplied artifact bytes were authorized for this project, stored, hashed, manifested, and audited.

It does **not** mean the artifact is scientifically correct, included, final, publishable, or advisor-approved.

## 9. Death-test requirements

PR-11 must fail closed for:

- exact foreign `export_id` across workspaces;
- exact foreign `export_id` across projects in the same workspace;
- reviewer/guest attempting export or audit;
- platform admin attempting private access without membership;
- researcher/viewer export without explicit project policy grant;
- path traversal in artifact name;
- unsupported media type;
- duplicate artifact names;
- artifact body appearing in the platform SQLite metadata store;
- artifact bytes modified after export;
- audit-event row modified after persistence;
- request body attempting to supply tenant/project/application identity.

## 10. Migration impact

None.

PR-11 does not attach historical artifacts to a workspace/project and does not consume the PR-7 migration planner as evidence of ownership.

The real historical dry-run still requires read-only access to the production `project_output*` volume. Article 2 remains blocked until its historical binding is separately validated.

## 11. Rollback

Revert PR-11 code and route registration.

New export custody files/tables are additive and contain only artifacts created through this new surface; no legacy scientific artifact is moved or rewritten by this PR.
