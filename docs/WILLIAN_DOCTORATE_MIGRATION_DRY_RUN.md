# First-party doctorate migration — PR-7 dry-run gate

## Purpose

PR-7 plans the first real customer migration into the multi-tenant platform model without mutating the historical scientific estate.

Target logical composition:

```text
Owner: Willian
└── Workspace: Doutorado Willian — UnB
    ├── Project: Artigo 1
    │   └── ApplicationTemplate: SCOPING_REVIEW
    └── Project: Artigo 2
        └── ApplicationTemplate: INTEGRATIVE_REVIEW
```

These are **logical proposed targets only** in PR-7.

No user/workspace/project/application IDs are created or inferred by the dry-run.

## Non-negotiable boundary

PR-7 does not:

```text
create users
create workspaces
create projects
create ResearchApplication rows
copy files
move files
rename files
rewrite article_id
execute searches
rerank results
recalculate scientific outputs
change screening decisions
change extraction
change reviewer decisions
recreate PRISMA
write Drive
write the platform database
```

The planner produces one artifact outside the legacy roots:

```text
LEGACY_MIGRATION_MANIFEST.json
```

## Generic planner vs first-party profile

The reusable planner is:

```text
src/nutev/migration/legacy_plan.py
```

It knows only:

```text
MigrationPlan
LogicalTarget
MappingRule
OwnershipClass
source paths
hashes
blockers
reference-only actions
```

It intentionally consumes the PR-0 ownership vocabulary, including `WILLIAN_PRIVATE`, `ARTICLE1_PRIVATE`, and `ARTICLE2_PRIVATE`, because those are inventory classes already established by the migration contract.

What it does **not** contain are the concrete first-party hierarchy, project labels, runtime paths, target keys, or manuscript-specific mapping rules. Those live only in the reviewed profile:

```text
src/nutev/migration/profiles/willian_doctorate.py
```

This preserves the architecture rule that customer applications/configuration do not define the scientific Engine.

## Ownership classes

The migration planner uses the PR-0 vocabulary:

```text
GLOBAL
WILLIAN_PRIVATE
ARTICLE1_PRIVATE
ARTICLE2_PRIVATE
SYSTEM
UNKNOWN
```

Only explicit private classifications may receive a logical private target.

`UNKNOWN` always produces:

```text
migration_action = NO_AUTOMATIC_MIGRATION
logical_target_key = null
```

## Reviewed built-in A1 evidence

PR-0 already established these runtime paths as A1-specific:

```text
agent_context/article1/*
scientific/review_routes/<search_id>/article1/*
```

The first-party profile maps them to:

```text
article1_project
```

by reference only.

## Validation database

PR-0 classified:

```text
16_validation_server/validation.sqlite3
```

as private Willian/project-to-demonstrate state.

PR-7 therefore maps it only to the doctorate workspace boundary:

```text
doctorate_workspace
```

It does **not** infer Article 1 or Article 2 ownership for this database.

HumanReviewEngine migration remains a later PR.

## Article 2 is intentionally fail-closed

PR-0 did not locate a first-class Article 2 namespace in the versioned repository.

Therefore PR-7 contains no heuristic such as:

```text
search name contains 2
query resembles Article 2
folder says busca2a
folder says busca2b
current user is Willian
current browser session created the search
```

None of these is sufficient ownership evidence.

Without an explicit reviewed runtime mapping, the manifest contains:

```text
REQUIRED_TARGET_NOT_MATERIALIZED: article2_project
```

and status:

```text
DRY_RUN_REVIEW_REQUIRED
```

## Explicit mapping

An operator-reviewed mapping file may add evidence-backed rules:

```json
{
  "schema_version": 1,
  "rules": [
    {
      "pattern": "reviewed/runtime/article2/*",
      "classification": "ARTICLE2_PRIVATE",
      "target_key": "article2_project",
      "evidence": "Concrete provenance demonstrating that this runtime path is Article 2 state"
    }
  ]
}
```

Every explicit rule requires a non-empty evidence statement.

Conflicting profile/explicit mappings do not override each other. They create:

```text
MAPPING_CONFLICT
DRY_RUN_FAIL
```

## Hash preservation

For every regular source file:

```text
source_sha256_before
source_sha256_after
source_unchanged
```

are recorded.

The planner computes all `before` hashes, performs only in-memory planning, then computes all `after` hashes.

Any mismatch creates:

```text
SOURCE_SHA_MISMATCH
DRY_RUN_FAIL
```

## Output location

The report path must be outside every legacy source root.

This is rejected:

```text
project_output_reference/LEGACY_MIGRATION_MANIFEST.json
```

A valid example is:

```text
./migration_reports/LEGACY_MIGRATION_MANIFEST.json
```

The output itself must not alter the estate whose hashes are being audited.

## CLI

The only command added by PR-7 is dry-run-only:

```bash
python tools/plan_multitenant_legacy_migration.py \
  --profile first-party-doctorate-v1 \
  --source-root /path/to/project_output_reference \
  --mapping /path/to/reviewed_mapping.json \
  --report /path/outside/source/LEGACY_MIGRATION_MANIFEST.json \
  --dry-run
```

No `--activate` or `--apply` option exists.

## Status contract

```text
DRY_RUN_PASS
```

All source files relevant to the inspected roots are explicitly classified, hashes are stable, no mapping conflicts exist, and required A1/A2 targets both have explicit evidence.

```text
DRY_RUN_REVIEW_REQUIRED
```

No mutation occurred, but at least one ownership gap remains, including UNKNOWN files or a required target without evidence.

```text
DRY_RUN_FAIL
```

A hard safety invariant failed, such as mapping conflict or source hash mismatch.

```text
SOURCE_NOT_MATERIALIZED
```

The real legacy volume/files are not mounted; this is not a successful migration test.

## What CI can prove

Repository CI can prove with fixtures:

- planner is read-only;
- hashes remain stable;
- known A1 paths map only to A1;
- A2 is not inferred;
- explicit A2 mapping works when evidence is supplied;
- unknown files are excluded;
- cross-project mapping conflicts fail closed;
- report cannot be placed inside source roots;
- generic planner contains no concrete first-party target labels, runtime paths, or target keys;
- no activation CLI exists.

## What CI cannot prove

The Git clone does not contain the real ignored `project_output*` production volume.

Therefore a green PR-7 CI **does not mean the real historical estate was migrated or even fully inventoried**.

After merge, the next operational gate is:

1. mount/access the actual legacy `project_output*` volume read-only;
2. run this exact dry-run against it;
3. review every `UNKNOWN`, conflict, and required-target blocker;
4. add only evidence-backed mapping rules;
5. repeat until the manifest is reviewable;
6. validate hashes and target counts;
7. only in a later, separately reviewed PR design `ACTIVATE`.

## Activation is deliberately out of scope

PR-7 ends at **DRY RUN / VALIDATE evidence**.

There is no cutover code in this PR.

That prevents a green unit test from silently becoming permission to attach legacy scientific state to a tenant.
