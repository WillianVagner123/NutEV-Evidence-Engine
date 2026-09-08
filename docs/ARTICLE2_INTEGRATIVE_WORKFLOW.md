# Article 2 — Integrative Review workflow · PR-10

## Purpose

PR-10 creates the private Article 2 integrative-review assembly using the same multi-tenant platform primitives already built for every research project.

It does **not** claim that the historical Article 2 estate has been identified or migrated.

Target application contract:

```text
Project: Artigo 2
ApplicationTemplate: INTEGRATIVE_REVIEW
assembly_id: WILLIAN_DOCTORATE_A2
integrative_config_version: a2-integrative-v1
```

The reusable Engine remains manuscript-agnostic.

---

## Why the workflow starts blocked

Repository inventory did not prove a first-class Article 2 runtime namespace.

Historical labels such as:

```text
busca2a
busca2b
```

are taxonomic/workstream remnants and are not sufficient ownership evidence.

PR-10 therefore starts every first-party A2 workflow as:

```text
current_phase = LEGACY_BINDING
workflow_status = BLOCKED
legacy_binding_state = REQUIRED_UNMATERIALIZED
```

No user action can bypass this state through HTTP.

---

## Reused platform composition

The existing public `INTEGRATIVE_REVIEW` template already composes:

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

PR-10 does not duplicate Article 1/D-132 implementation.

The A2 assembly only maintains private workflow state and evidence-backed phase transitions.

---

## Workflow phases

Configured sequence:

```text
LEGACY_BINDING
SEARCH_STRATEGY
SEARCH_EXECUTION
DEDUPLICATION
TITLE_ABSTRACT_SCREENING
FULL_TEXT
EXTRACTION
HUMAN_VERIFICATION
SYNTHESIS
COMPLETE
```

A phase cannot be skipped.

Advancing a phase requires a non-empty evidence statement. Only its SHA-256 digest is stored in the workflow audit event.

The workflow service itself does not execute searches, deduplication, screening, extraction or synthesis. Those remain operations of existing reusable Engine services. The phase record only captures reviewed orchestration state.

---

## Legacy binding contract

The internal binding primitive accepts only a reviewed `LegacyBindingEvidence` object:

```text
manifest_sha256
target_key = article2_project
classification = ARTICLE2_PRIVATE
record_count > 0
source_fingerprints[] = SHA-256 digests
evidence = reviewed provenance statement
validation_status = VALIDATED
```

It deliberately does **not** accept:

```text
filesystem path
query text
search_id
browser/session owner
current login
workstream name
busca2a/busca2b inference
```

The binding fingerprint is a SHA-256 digest of the reviewed evidence contract.

---

## No binding HTTP endpoint

Public/pilot A2 routes are limited to:

```text
POST /api/article2/integrative/bootstrap
GET  /api/article2/integrative/status
GET  /api/article2/integrative/events
POST /api/article2/integrative/advance
```

There is intentionally no:

```text
/bind
/legacy-binding
/activate
/migrate
```

`register_legacy_binding()` is an internal migration hook for a later reviewed activation step after the real PR-7 runtime inventory/dry-run is available.

---

## Tenant/project authorization

The HTTP adapter derives identity from the authenticated server-side session and current project context.

It does not accept `workspace_id`, `project_id` or `application_id` from the request body.

The active project must have:

```text
template_id = INTEGRATIVE_REVIEW
configuration.assembly_id = WILLIAN_DOCTORATE_A2
configuration.integrative_config_version = a2-integrative-v1
```

Knowing an A2 endpoint or workflow ID is not ownership evidence.

---

## Private storage

New tables:

```text
article2_integrative_meta
article2_integrative_workflows
article2_integrative_events
```

They store only:

```text
workspace/project/application identity
workflow phase/status
binding fingerprint
phase-evidence hashes
timestamps
actor pseudonymous user ID
```

They do not store:

```text
query
search_id
filesystem path
document body
abstract
full text
Article 1 project identity
```

Scientific artifacts remain in their existing primitives/registries and are related to the project only through explicit tenant-scoped ownership structures.

---

## Scientific non-effects

Bootstrap/binding/orchestration in PR-10 do not themselves:

```text
execute search
recalculate historical results
rewrite article_id
copy legacy files
import Article 1 state
change screening
change extraction
change synthesis
create PRISMA
```

The status response explicitly reports these side effects as false.

---

## Current historical migration status

At PR-10 implementation time:

```text
Article 2 historical ownership = NOT MATERIALIZED / NOT ACTIVATED
```

This is not inferred from prior count memories or old workstream names.

The correct sequence remains:

```text
real project_output* read-only inventory
→ explicit Article 2 mapping evidence
→ reviewed migration validation
→ internal LegacyBindingEvidence
→ only then workflow leaves LEGACY_BINDING
```

The real production-volume dry-run is still operationally blocked by the invalid Hetzner `HETZNER_SSH_KEY` secret. A green repository PR does not change that fact.

---

## Tests / death tests

PR-10 covers:

```text
config requires INTEGRATIVE_REVIEW
initial workflow is BLOCKED
cannot advance without binding
wrong target/classification rejected
invalid/duplicate source hashes rejected
non-VALIDATED evidence rejected
valid internal binding activates SEARCH_STRATEGY
no scientific payload columns in A2 store
phase skipping denied
phase evidence required and stored only by hash
same-workspace projects remain isolated
PLATFORM_ADMIN does not bypass APPLICATION_MANAGE
HTTP has no binding/activation endpoint
HTTP body cannot supply tenant/project/application/search identity
A2 assembly does not import A1 adapter
A2 assembly does not import search engine
busca2a/busca2b are never runtime ownership rules
```

---

## Backwards compatibility

PR-10 does not alter:

```text
Article 1 / D-132
HumanReviewEngine
search providers
Global Registry
Workbench
legacy validation.sqlite3
historical project_output* files
```

---

## Rollback

Revert PR-10.

No historical A2 artifact is moved or mutated, so there is no scientific rollback operation.

---

## Next step

After PR-10 is green, the planned sequence continues to:

```text
PR-11 — Export Project
PR-12 — tenant/security death test
PR-13 — controlled production migration/deploy
```

The real Article 2 historical binding remains a separate migration gate and cannot be declared complete until its runtime evidence exists.
