# NutEV multi-tenant — ResearchApplication / ApplicationTemplate

## Status

PR-6 introduces the project application layer only.

It does **not** migrate Article 1, Article 2, Workbench, searches, screening, extraction, PRISMA, or historical files.

## Architectural rule

```text
Evidence Engine
    ↓ reusable scientific operations
ApplicationTemplate
    ↓ reusable composition
ResearchApplication
    ↓ private project configuration
Project
```

The Engine knows operations, not individual manuscripts.

A template is reusable platform knowledge. A ResearchApplication is project-owned configuration.

## Existing model reused

PR-1 already introduced `ResearchApplication` with:

```text
id
project_id
application_type
template_id
config_version
status
created_at
```

PR-6 does not create a second competing model. It adds persistence, template version binding, private configuration, authorization, and API access around the existing contract.

## Built-in starter templates

Initial reusable templates:

```text
GENERIC_EVIDENCE_PROJECT
SCOPING_REVIEW
INTEGRATIVE_REVIEW
```

Templates are deliberately small and compositional.

### GENERIC_EVIDENCE_PROJECT

```text
RESEARCH_QUESTION
SEARCH
NORMALIZE
TRACEABILITY
DEDUPLICATE
ORGANIZE
HUMAN_VERIFICATION
SYNTHESIS
```

No review-method mandate is implied.

### SCOPING_REVIEW

Starter composition:

```text
PCC
SEARCH
DEDUPLICATION
TITLE_ABSTRACT_SCREENING
FULL_TEXT
EXTRACTION
HUMAN_VERIFICATION
SYNTHESIS
PRISMA_SCR
```

This is a reusable starter, not a substitute for the project's protocol or methodological decisions.

### INTEGRATIVE_REVIEW

Starter composition:

```text
RESEARCH_QUESTION
SEARCH
DEDUPLICATION
TITLE_ABSTRACT_SCREENING
FULL_TEXT
EXTRACTION
HUMAN_VERIFICATION
SYNTHESIS
```

Project-specific appraisal, reporting, eligibility, extraction, and synthesis settings remain private configuration.

## No closed application-type enum

The Engine must remain extensible.

A project may configure a custom application type without modifying a global enum:

```text
CUSTOM
RAPID_REVIEW
SYSTEMATIC_REVIEW
EVIDENCE_MAP
LITERATURE_COLLECTION
future application type
```

Built-in templates are a catalog, not the universe of valid ResearchApplications.

`ApplicationTemplateCatalog` can also receive injected future templates.

## Template immutability

`ApplicationTemplate` is frozen and stores defaults as serialized data.

Project configuration receives a detached copy.

Therefore:

```text
Project A configuration mutation
    ≠ template mutation
    ≠ Project B mutation
```

## Global/public template state

A reusable template may contain:

```text
template ID
version
name
description
application type
component list
safe default configuration
visibility
```

It must not contain project/customer scientific state.

Forbidden in built-in templates:

```text
Willian's research question
Willian's documents
Article 1 decisions
Article 2 decisions
private notes
screening decisions
extractions
reviewer decisions
D-132 private state
ABCD-NutEV private state
results
manuscripts
PRISMA counts
```

## Private ResearchApplication state

The platform DB table `platform_research_applications` stores project-owned configuration:

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

`configuration_json` is private project state and may contain the project's actual question, options, enabled components, method settings, and other project configuration.

It is never promoted back into the reusable template.

## One current application per project

PR-6 models the current project contract as one active ResearchApplication per project.

Reconfiguration preserves the opaque application ID and updates the private configuration/version.

This does not prevent a future explicit application-version/history table; PR-6 avoids inventing historical scientific events before the migration contract exists.

## Authorization

Explicit permissions:

```text
application.read
application.manage
```

Role matrix for this layer:

```text
                          READ   MANAGE
WORKSPACE_OWNER            yes     yes
WORKSPACE_ADMIN            yes     yes
RESEARCHER                 yes     yes
VIEWER                     yes      no
REVIEWER                    no      no
GUEST_REVIEWER              no      no
PLATFORM_ADMIN*             no      no
```

`PLATFORM_ADMIN` remains infrastructure-only unless it has an explicit workspace membership/authorized support path.

Both permissions are project-scoped and require confirmed project access.

## API

Authenticated pilot routes:

```text
GET  /api/application/templates
GET  /api/application
POST /api/application
```

### Template list

Returns reusable template descriptors only.

It does not return private project configuration.

### Current application

`GET /api/application` derives the target from the authenticated session's current workspace/project.

### Configure current application

`POST /api/application` accepts application/template/config fields only.

A client-supplied `project_id`, `workspace_id`, or `user_id` is not used as the authorization target.

The authoritative target is:

```text
Session
→ Principal
→ current workspace
→ current project
→ project access
→ application permission
```

This prevents an IDOR where a client knows another project's ID.

## Scientific impact

PR-6 changes no scientific engine behavior:

```text
NO provider change
NO query change
NO ranking change
NO deduplication change
NO Registry identity change
NO search rerun
NO screening execution
NO extraction execution
NO reviewer decision change
NO PRISMA event
NO A1 mutation
NO A2 mutation
```

Templates describe composable paths; they do not execute or approve scientific decisions by themselves.

## Migration boundary

PR-6 does **not** create:

```text
Willian
└── Doutorado
     ├── Article 1 → SCOPING_REVIEW
     └── Article 2 → INTEGRATIVE_REVIEW
```

That is PR-7 and must use the migration dry-run / validate / activate process.

No name, project ID, application ID, question, or result belonging to Willian is hardcoded in PR-6.

## Death tests

Required coverage:

```text
same template in Tenant A and Tenant B
→ same reusable template
→ independent ResearchApplication IDs
→ independent private configuration

tenant B knows A IDs
→ no A application access

Viewer
→ read current application
→ configure denied

Reviewer
→ no project-wide application access

custom application type
→ accepted without Engine enum change

malicious POST project_id=A while session context=B
→ target remains B

template descriptor
→ no A/B private question
→ no A1/A2/Willian private state
```

## Rollback

1. revert PR-6;
2. application rows become unused platform metadata;
3. existing workspace/project/search/library layers remain intact;
4. no scientific state needs recalculation;
5. no historical migration needs rollback because PR-6 performs none.
