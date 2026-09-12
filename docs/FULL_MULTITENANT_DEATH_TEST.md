# NutEV — Full Multi-tenant Death Test

Status: **current hermetic release/security gate**.

## Objective

Prove that independent tenants can reuse the same NutEV Engine and global bibliographic identity without sharing private operational/scientific state.

The scenario is destructive only inside a fresh temporary fixture. It does not connect to production, call external providers, execute formal scientific searches or activate historical ownership.

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

Both projects reuse the same global document identity while every private layer remains tenant/project scoped.

## Covered boundaries

The gate crosses the product's main private boundaries in one scenario:

1. authentication/session identity;
2. workspace/project context;
3. search ownership/history;
4. Evidence Library placement/full-text grants;
5. ResearchApplication configuration;
6. Human Review assignments/decisions/locks;
7. Export and audit custody;
8. PLATFORM_ADMIN non-bypass of tenant-private state.

Exact foreign IDs are exercised wherever possible so anti-enumeration is tested against a real existing resource rather than only a random unknown ID.

## Execution

```bash
python tools/multitenant_death_test.py
```

Optional report:

```bash
python tools/multitenant_death_test.py --output /tmp/nutev-tenant-death.json
```

The tool creates its operational state under a fresh `TemporaryDirectory` and has no production-host, SSH, migration-apply or ownership-activation option.

## PASS contract

A successful report identifies:

```text
record_type = NUTEV_FULL_MULTITENANT_DEATH_TEST
schema_version = 1
status = PASS
tenant_count = 2
project_count = 2
```

It also asserts, among other properties:

```text
no_network_required = true
temporary_fixture_only = true
historical_ownership_modified = false
scientific_search_executed = false
article1_state_modified = false
article2_legacy_binding_modified = false
platform_admin_private_bypass = false
```

Every required death check must pass independently.

## Scientific non-impact

The hermetic gate does not mutate production Registry/Workbench data, formal Article 1 state, D-132 source/decisions, PRESS/GF-10/query freeze, Article 2 legacy binding, PRISMA, production Human Review decisions or production exports.

A PASS proves the tested isolation/security contracts in the disposable scenario. It does not by itself prove that a particular production SHA has been deployed or that a scientific methodology is valid.

## Promotion relationship

The death test is one prerequisite of the exact-SHA production release gate. Production promotion additionally requires the normal CI/security/artifact/browser gates, recovery readiness, successful Hetzner deployment, runtime/edge verification and exact deployed commit identity described in [`FINAL_MULTITENANT_RELEASE_GATE.md`](FINAL_MULTITENANT_RELEASE_GATE.md).
