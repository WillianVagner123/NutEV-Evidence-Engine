# Article 2 — read-only legacy runtime inventory

## Purpose

This workflow closes the **observation** gap that previously blocked Article 2 legacy review. It inventories candidate `project_output*` trees on the production host and the current runtime container without assigning ownership.

It is **not** `LegacyBindingEvidence`, does not activate Article 2, and does not create scientific state.

## Run

GitHub Actions:

`article2-legacy-runtime-inventory`

Run it manually from `main` after the exact candidate SHA has passed the repository gates.

The workflow uses the existing protected `HETZNER` environment and pinned SSH host identity.

## Output

The private workflow artifact contains:

`article2-legacy-runtime-inventory.json`

For every candidate it records only structural evidence:

- opaque candidate/location fingerprints;
- content-derived tree SHA-256;
- file count and total bytes;
- extension counts;
- safe allowlisted metadata from JSON manifest/audit files;
- count of skipped symlinks.

It does **not** expose raw filesystem paths, query text, search IDs or document bodies.

Every candidate remains:

```text
ownership = UNKNOWN_UNTIL_REVIEW
classification_inferred = false
```

and the bundle remains:

```text
legacy_binding_performed = false
binding_status = NOT_CREATED_REVIEW_REQUIRED
```

## Review sequence

The inventory supports, but does not replace, the human provenance review:

```text
runtime inventory
  -> compare candidate fingerprints/manifests with reviewed external provenance
  -> classify GLOBAL / ARTICLE1_PRIVATE / ARTICLE2_PRIVATE / WILLIAN_PRIVATE / SYSTEM / UNKNOWN
  -> document record counts and mapping
  -> validate provenance
  -> create internal LegacyBindingEvidence only for proven ARTICLE2_PRIVATE material
  -> register binding through the existing internal migration primitive
```

A directory name, `busca2a`, `busca2b`, current login, query text or search ID is never sufficient ownership evidence.

## Scientific boundary

This workflow performs no search, screening, PRISMA event, PRESS/GF change, extraction, synthesis or result recalculation. A successful inventory means only that the runtime estate was observed reproducibly.
