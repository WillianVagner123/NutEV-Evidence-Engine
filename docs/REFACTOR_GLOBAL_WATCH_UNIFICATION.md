# Phased Migration — Unify Global Watch with the search orchestrator

> **Status: planned (not started).** Design/migration plan, not executed work.
> Global Watch keeps a second, parallel search stack; merging it with the main
> `search.provider_orchestrator` changes what queries run, so it must be phased
> and parity-gated, not rewritten at once.

## Why this exists

`src/nutev/global_watch/` runs its **own** search stack, independent of the main
pipeline's `search.provider_orchestrator`:

- **Its own query builder** — `watch_query_builder.py` (~1,445 LOC):
  `build_watch_queries()` + category/context-term construction, distinct from
  the `querypacks/` builders the master pipeline uses.
- **Its own provider dispatch** — `watch_pipeline._build_provider_map()`
  (line 593) calls the low-level connector functions directly
  (`search_pubmed(q, retmax=12)`, `search_europepmc(q, page_size=12)`,
  `search_openalex(...)`, optional `search_crossref(...)`), **bypassing**
  `search_provider()` / `_registry()`.
- **Its own run/event/perf instrumentation** — `run_watch_provider()` (line 617)
  re-implements provider start/skip/complete events and timing that the
  orchestrator already provides via `search_provider()`.

**The problem.** Two code paths reach the same connectors with different limits,
retry/backoff, checkpointing, event logging and (crucially) **different generated
queries**. Bugs and improvements must be made twice; the two stacks can drift.

## What is already safe (done)

Audit finding **T6** added `watch_provider_ids()` (line 604) and a reconciliation
guard (`nutev_tests/test_watch_provider_reconcile.py`) so the two stacks can
never disagree about **which** providers exist. This migration addresses the
remaining duplication (dispatch, instrumentation, and eventually query building).

## Why it can't just be merged

1. **It changes scientific outputs.** `watch_query_builder` generates *different*
   queries than `querypacks`; making Global Watch use the main query builder would
   change what Global Watch retrieves. Query-building unification (Phase 3) is the
   highest-risk step and may be deliberately **declined** — the two products
   (periodic watch vs. systematic review) can legitimately want different queries.
2. **Different limits/semantics.** Watch uses small per-provider caps
   (`retmax=12`, `page_size=12`, `per_page=10`, `rows=10`) tuned for frequent,
   shallow sweeps; the orchestrator is tuned for systematic depth. Unifying
   dispatch must preserve Watch's caps.
3. **The watch pipeline is large and self-contained** (`watch_pipeline.py` ~946,
   `watch_scoring.py` ~899, `watch_query_builder.py` ~1,445). Changes need the
   Global Watch integration tests (`test_watch_pipeline_real.py`,
   `test_global_watch_dedup.py`, `test_watch_config*`) green at every step.

## Guiding principles

- **Parity gate every phase.** A fixed offline Global Watch run must produce
  identical hits/scoring/digest before and after each phase.
- **Preserve Watch's tuning.** Same per-provider caps, same dedup, same scoring.
- **Adopt the orchestrator's *mechanism*, not its *parameters*.**

## Phases

### Phase 0 — Parity harness (prerequisite)
- Golden offline Global Watch run (mocked connectors) snapshotting hits, scoring
  and the digest. **Acceptance:** harness green; snapshot committed as reference.

### Phase 1 — Dispatch through `search_provider` (mechanism only)
- Replace `_build_provider_map()` + `run_watch_provider()` internals so each
  provider call goes through `search.provider_orchestrator.search_provider(...)`,
  passing Watch's existing caps as the `limit` and a Watch-specific
  `checkpoint_dir`/`logs_dir`. Keep Watch's query builder untouched.
- Benefit: one instrumentation path (events, `provider_performance.csv`,
  `provider_failures.csv`, retry/backoff, retrieval-date stamping from C8) for
  both stacks. **Acceptance:** hits/scoring/digest byte-identical to Phase 0;
  `run_watch_provider` no longer imports low-level `search_*` directly.

### Phase 2 — Shared result normalization
- Route Watch results through the same normalization the orchestrator/connectors
  already apply, removing any Watch-local duplicate of row shaping.
  **Acceptance:** parity preserved; duplicate normalization deleted.

### Phase 3 — Query building (OPTIONAL, decision required)
- Evaluate whether Global Watch should reuse the `querypacks`/strategy builder or
  keep `watch_query_builder`. This **changes retrieved results**, so it is a
  product decision, not a refactor. If declined, document that the divergence is
  intentional and stop here. If accepted, migrate behind a flag with its own
  parity/coverage comparison (recall before/after), never silently.

## Rollback

Each phase is a separate PR, parity-gated against the Phase 0 snapshot. A
regression is caught before merge; otherwise revert the single PR to restore the
previous Watch behavior.

## Definition of done

Global Watch shares the orchestrator's dispatch, instrumentation and
normalization (Phases 1–2), with the reconciliation guard (T6) preventing
provider drift. Query-building unification (Phase 3) is either done behind an
explicit, measured decision or explicitly declined and documented — never an
accidental change to what Global Watch retrieves.
