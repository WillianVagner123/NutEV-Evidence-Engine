# NutEV — ResearchApplication / ApplicationTemplate Contract

Status: **current v1.1.0 hosted-product contract**.

## Architectural rule

```text
Evidence Engine
    ↓ reusable scientific operations
ApplicationTemplate
    ↓ reusable composition/defaults
ResearchApplication
    ↓ private project configuration
Project
```

The reusable Engine does not know individual manuscripts or customers. A template is reusable platform configuration; a ResearchApplication is private project-owned state.

## Built-in starter templates

The current catalog includes:

```text
GENERIC_EVIDENCE_PROJECT
SCOPING_REVIEW
INTEGRATIVE_REVIEW
```

Templates are starters, not methodological approval. Projects may use custom application types/configurations without converting manuscript-specific logic into a global Engine rule.

A template may contain safe reusable defaults such as component lists and configuration schema. It must not contain a customer's research question, private notes, screening/extraction decisions, reviewer judgments, PRISMA counts, manuscript results or private Article 1/Article 2 state.

## Private ResearchApplication state

`platform_research_applications` stores the active project application, including:

```text
id
project_id
application_type
template_id
template_version
config_version
configuration_json
status
created_by
created_at
updated_at
```

The project configuration is private and detached from the reusable template. Updating Project A must not mutate the template or Project B.

The current platform models one current ResearchApplication per project. Reconfiguration preserves the application's opaque identity while updating its private configuration/version according to the service contract.

## Authorization

Application operations are project-scoped and require server-confirmed project access plus the relevant application permission.

Typical role behavior:

```text
WORKSPACE_OWNER   read/manage
WORKSPACE_ADMIN   read/manage
RESEARCHER        read/manage
VIEWER            read only
REVIEWER          no project-wide application access
GUEST_REVIEWER    no project-wide application access
PLATFORM_ADMIN    no implicit private-project bypass
```

## API

Hosted authenticated routes include:

```text
GET  /api/application/templates
GET  /api/application
POST /api/application
```

The target project is derived from the authenticated session context. Client-supplied `workspace_id`, `project_id` or `user_id` is not accepted as proof of ownership.

```text
Session
→ Principal
→ current workspace
→ current project
→ project access
→ application permission
```

The onboarding flow uses these same primitives. Creating/configuring the first project application must persist across refresh and logout/login; that behavior is covered by the authenticated Chromium regression gate.

## First-party scientific applications

Article 1 and Article 2 may use specialized private adapters/assemblies on top of the generic platform. Those adapters do not become defaults for unrelated tenants or templates.

Repository configuration, route availability or an `assembly_id` alone does not establish historical scientific ownership. Any legacy binding/provenance activation remains separately evidence-gated and fail-closed.

## Scientific boundary

Configuring a ResearchApplication does not itself:

```text
execute a provider search
change query/ranking/deduplication semantics
include or exclude records
perform extraction or adjudication
approve PRESS / GF-10 / query freeze
activate historical ownership
create PRISMA events
approve synthesis/recommendations
```

Those effects, where supported, belong to their explicit scientific operations and human/governance gates.
