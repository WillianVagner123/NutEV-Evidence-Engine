# NutEV — Full Multi-tenant Death Test

Status: PR-12 release gate.

## Objective

Prove, in one hermetic scenario, that two independent tenants can reuse the same NutEV scientific engine and the same global bibliographic identity without sharing private operational or scientific state.

The gate is intentionally destructive only inside a temporary fixture directory.

It does not connect to production, does not call providers, does not execute scientific searches, and cannot activate historical ownership.

## Fixture

```text
Tenant A
  Workspace A
    Project A
      SCOPING_REVIEW

Tenant B
  Workspace B
    Project B
      INTEGRATIVE_REVIEW

Global Evidence Registry
  one shared article_id
```

Both projects use the same global document identity. Every private layer must remain independent.

## Matrix

The single scenario crosses these boundaries:

1. Identity
   - distinct users;
   - correct password authenticates;
   - wrong password fails.

2. Workspace / project context
   - each session selects its own workspace/project;
   - Tenant A cannot select Tenant B's workspace/project even with exact IDs.

3. Search ownership
   - distinct job IDs and search IDs;
   - project history contains only its own search;
   - exact foreign job/search ID fails closed;
   - an unowned historical-like search ID is not automatically adopted.

4. Evidence Library
   - the same global `article_id` is reusable by both tenants;
   - Placement IDs differ;
   - private state/tags/notes remain independent;
   - exact foreign Placement ID fails closed;
   - full-text grant created by A is invisible to B;
   - internal cache path is absent from the public grant descriptor.

5. ResearchApplication
   - A uses `SCOPING_REVIEW`;
   - B uses `INTEGRATIVE_REVIEW`;
   - configuration remains private;
   - exact foreign workspace/project context fails closed.

6. Human Review
   - independent rounds, reviewers and assignments;
   - field allowlist hides private payload fields;
   - exact foreign round ID fails closed;
   - exact foreign assignment ID fails closed;
   - submit locks the decision against later mutation.

7. Export / Audit
   - independent export IDs and application bindings;
   - project export listing shows only local exports;
   - exact foreign export ID fails closed;
   - each project audit chain validates independently.

8. Platform administration
   - a `PLATFORM_ADMIN` principal with no workspace membership cannot bypass private search, library, application or export boundaries.

## Execution

Hermetic CLI:

```bash
python tools/multitenant_death_test.py
```

Optional report destination:

```bash
python tools/multitenant_death_test.py --output /tmp/nutev-tenant-death.json
```

The CLI always creates its operational data under a fresh `TemporaryDirectory`.

It deliberately has no options for:

```text
project_output_reference
production database
remote host
SSH
public URL
historical source root
migration apply
ownership activation
```

## PASS contract

A successful report must contain:

```json
{
  "record_type": "NUTEV_FULL_MULTITENANT_DEATH_TEST",
  "schema_version": 1,
  "status": "PASS",
  "tenant_count": 2,
  "project_count": 2,
  "assertions": {
    "no_network_required": true,
    "temporary_fixture_only": true,
    "historical_ownership_modified": false,
    "scientific_search_executed": false,
    "article1_state_modified": false,
    "article2_legacy_binding_modified": false,
    "platform_admin_private_bypass": false
  }
}
```

Every listed death check must independently report `PASS`.

## Scientific non-impact

This gate does not mutate:

```text
Global Registry production records
Workbench
formal Article 1 search state
D-132 canonical sample
PRESS / GF-10 / query freeze
Article 2 legacy binding
PRISMA
Human Review production decisions
production exports
```

The Registry fixture is synthetic and exists only in the temporary test directory.

## Relation to PR-13

PR-12 is the hermetic release gate. PR-13 still requires a production/public smoke after deployment with the deployed SHA, authentication boundary, provider/search availability, private A1/A2 access and version endpoint verified against the actual runtime.

A PASS here does not prove that the current production host is deployed or reachable.
