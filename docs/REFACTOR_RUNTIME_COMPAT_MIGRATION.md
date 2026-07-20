# Phased Migration — Dissolve the `runtime_compat` shim layer

> **Status: in progress.** Phase 0 (parity harness) and Phase 1 (query generation
> → querypacks) are **done**; Phases 2–5 remain. `runtime_compat` cannot be
> removed in a single change without risking the scientific outputs and the test
> suite, so each phase is independently shipped and gated on **parity** (same
> input → same outputs).
>
> - ✅ **Phase 0** — `nutev_tests/test_runtime_compat_parity.py` + baseline.
> - ✅ **Phase 1** — terms moved to `querypacks/builders.EXTRA_BOOLEAN_QUERIES` and
>   `querypacks/provider_queries.PUBMED_WORKSTREAM_ANCHOR_TERMS`;
>   `_patch_query_generation` deleted from `apply()`. Parity gate green.

## Why this exists

`src/nutev/runtime_compat.py` monkey-patches core functions **at runtime** via a
single idempotent `apply()` (invoked from `cli.main()` and, since audit finding
T1b, from `run_pipeline()` itself). `apply()` installs five patches:

| Patch | What it wraps | What it injects |
|-------|---------------|-----------------|
| `_patch_workstream_validation` | `engine.validators.validate_workstream` (+ `models`) | accepts `global_watch` as a valid workstream |
| `_patch_curation` | `export.curation.curate_outputs` | renames curated CSVs to `NUTEV_*`, writes legacy QA reports, and runs the **audit + convergence** stage (`write_audit_and_convergence`) into `02_metadata` / `06_tables` |
| `_patch_run_summary` | `export.logs.write_run_summary` | merges audit metrics (claims/recs/conflicts counts) into `run_summary.json` |
| `_patch_synthesis_defaults` | `analysis.synthesis.write_synthesis_outputs` | fills default evidence-priority columns on master rows |
| `_patch_query_generation` | `querypacks.provider_queries.render_queries_for_provider` and `querypacks.builders.build_queries` | **appends real PubMed search terms** per workstream (busca1/2a/2b/a3) and extra boolean queries |

**The problem.** Behavior that is scientifically load-bearing (query terms,
synthesis columns, the entire claims/recommendations layer) lives in a runtime
patch instead of the normal call graph. That is hard to read, hard to test in
isolation, and easy to break by import order. The audit flagged the *audit-stage*
part specifically (T1); T1b already removed the **fragility** (both `cli.main`
and `run_pipeline` now call `apply()`), but the patches themselves remain.

## Why it can't just be deleted

1. **It changes scientific outputs.** `_patch_query_generation` adds real query
   terms; removing it changes what PubMed returns → violates the reproducibility
   contract (same input → same outputs). Any migration MUST fold these terms into
   the querypack config/code so the generated queries are **byte-identical**.
2. **The test suite depends on it.** `nutev_tests/conftest.py` calls `apply()`
   for the whole session, and these tests assert on patched behavior:
   `test_curation_outputs`, `test_curation_phase5`, `test_audit_claims_path_contract`,
   `test_runtime_compat`, `test_query_expansion_patch`, `test_run_pipeline_self_apply`.
   Each must be migrated to the first-class API as its patch is dissolved.

## Guiding principles

- **Parity gate every phase.** Before/after a phase, a fixed offline input must
  produce identical artifacts (diff the `02_metadata` / `06_tables` / `07_logs`
  trees and the generated query lists). No phase merges until the diff is empty.
- **One patch per phase.** Never dissolve two patches in the same change.
- **Keep `apply()` working throughout.** Until the last patch is gone, `apply()`
  stays and remains idempotent; a dissolved patch becomes a no-op that logs once.
- **Move, don't rewrite.** Relocate the exact logic into the normal call graph;
  behavior changes are out of scope for this migration.

## Phases

### Phase 0 — Parity harness (prerequisite, no behavior change)
- Add a dev-only golden test: run the offline pipeline on a small fixed corpus,
  snapshot the output trees + generated query lists, assert byte-stability.
- Snapshot the current `apply()`-on baseline. **Acceptance:** the harness is
  green and its snapshot is committed as the reference every later phase diffs
  against.

### Phase 1 — Query generation → querypacks (highest scientific risk first)
- Move the per-workstream term lists and extra boolean queries from
  `_patch_query_generation` into `querypacks/` (config or code) so
  `render_queries_for_provider` / `build_queries` produce them natively.
- Migrate `test_query_expansion_patch` to assert the terms come from the real
  builder. **Acceptance:** generated query lists byte-identical to Phase 0;
  `_patch_query_generation` deleted from `apply()`.

### Phase 2 — Audit stage → first-class pipeline step
- `run_pipeline` calls `write_audit_and_convergence` (already extracted, tested)
  **directly** after `curate_outputs`, and merges the returned metrics into its
  own `summary` before `write_run_summary`.
- Move the curated-CSV renames + legacy QA reports (`_copy_if_exists`,
  `_legacy_reports`) into `export.curation` (or a small `curation_finalize`).
- Migrate `test_audit_claims_path_contract`, `test_curation_outputs`,
  `test_curation_phase5` to call the first-class path (drop `_patch_curation()`
  usage). **Acceptance:** output trees byte-identical to Phase 0;
  `_patch_curation` + `_patch_run_summary` deleted from `apply()`.

### Phase 3 — Synthesis defaults → synthesis module
- Fold the default evidence-priority columns into
  `analysis.synthesis.write_synthesis_outputs` (or its row builder).
  **Acceptance:** synthesis outputs byte-identical; `_patch_synthesis_defaults`
  deleted.

### Phase 4 — Workstream validation → validators
- Add `global_watch` to the accepted set in `engine.validators.validate_workstream`
  directly. **Acceptance:** `_patch_workstream_validation` deleted.

### Phase 5 — Retire the shim
- `apply()` now patches nothing. Remove `apply()` calls from `cli.main` and
  `run_pipeline`, delete `runtime_compat.py`, and rewrite `test_runtime_compat`
  into whatever coverage still applies (or delete it). Remove the `apply()` call
  from `conftest.py`. **Acceptance:** full suite green with no reference to
  `runtime_compat`; parity harness still byte-identical to Phase 0.

## Rollback

Each phase is a separate PR. Because every phase is parity-gated against the
Phase 0 snapshot, a regression is caught before merge; if one slips through,
revert that single PR — the shim for that patch is restored and the pipeline is
back to the previous behavior.

## Definition of done

`runtime_compat.py` no longer exists; every behavior it injected lives in the
normal call graph with its own tests; and the Phase 0 parity harness proves the
pipeline's scientific outputs never changed across the entire migration.
