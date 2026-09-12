# NutEV — Multi-tenant Export & Audit Contract

Status: **current v1.1.0 hosted-product contract**.

## Purpose

`ProjectExportAuditService` provides tenant/project custody for artifact bytes produced by an existing NutEV scientific/application primitive.

```text
existing scientific/application output
→ tenant/project authorization
→ artifact hashing
→ private project storage
→ export manifest
→ append-only hash-chained audit events
```

The export layer does not reinterpret evidence quality, eligibility, synthesis, certainty, recommendation, PRISMA counts or manuscript conclusions.

## Authorization

The target workspace/project/application is derived from the authenticated Principal and server-confirmed current context. Client-supplied ownership fields are not accepted as proof of access.

Relevant capabilities are scoped around export creation/read and audit inspection. `PLATFORM_ADMIN` remains infrastructure authority and is not an implicit private scientific-data bypass.

## Storage and manifest

Default private artifact layout is project-scoped under persistent output storage. The platform database stores export/audit metadata and hashes, not arbitrary artifact bodies.

Each export manifest records identifiers, creation metadata and artifact descriptors including:

```text
name
media_type
sha256
size_bytes
```

Internal storage paths are not exposed as public artifact descriptors.

## Artifact security

The hosted API accepts controlled artifact content produced for the current project and rejects path-based ownership tricks. Artifact names are constrained to safe single filenames, supported media types are allowlisted, and stored bytes are re-hashed before delivery.

A hash/size mismatch fails closed.

Responses containing private export material are non-cacheable/private and use content-type hardening.

## Audit chain

Security-relevant export actions append project-local audit events containing the previous event hash and a canonical SHA-256 event hash.

The chain makes later mutation detectable; it is an integrity mechanism, not a cryptographic signature or external timestamp authority.

Different projects maintain independent chains.

## HTTP surface

Hosted authenticated routes include:

```text
POST /api/exports
GET  /api/exports
GET  /api/exports/<export_id>/manifest
GET  /api/exports/<export_id>/artifacts/<name>
GET  /api/audit?limit=<n>
```

There is no generic cross-workspace export listing, path-ingestion endpoint or public historical-ownership activation endpoint.

## Fail-closed invariants

The release/death-test contract includes checks for:

- exact foreign export IDs across workspaces/projects;
- unauthorized reviewer/guest export access;
- infrastructure-admin access without tenant membership;
- export attempts without required policy grants;
- path traversal and unsupported media type;
- duplicate artifact names;
- modified artifact bytes;
- modified audit-chain rows;
- request bodies attempting to choose tenant/application ownership.

## Historical migration boundary

Creating an export does not attach pre-existing historical artifacts to the current tenant and does not establish Article 1/Article 2 legacy ownership. Historical custody remains a separate evidence/provenance question.

## Scientific boundary

A successful export means the supplied project-authorized bytes were stored, hashed, manifested and audited. It does **not** mean the content is scientifically correct, included, final, publishable or advisor-approved.
