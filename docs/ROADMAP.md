# Roadmap

High-level direction. Dates are indicative; scientific correctness and human
oversight take precedence over speed.

## v0.1.0-alpha (first public, organized release)

- [x] Public release audit (`docs/PUBLIC_RELEASE_AUDIT.md`).
- [x] Decouple package identity/version from legacy (`nutev` only).
- [x] Split core vs optional dependencies; zero-key demo.
- [x] Canonical test location `nutev_tests/` + test-group markers.
- [x] Open-science governance docs (governance, data, AI oversight, copyright,
      reproducibility).
- [x] Provenance: `NOTICE.md`, `CITATION.cff`, `CODE_OF_CONDUCT.md`.
- [ ] Harden public workflows + artifact sanitization + gitleaks in CI.
- [ ] Article 1 reproducible pilot (`examples/article1_pilot/`).
- [ ] Release checklist + install validation on Python 3.12.

## v0.2.0 — legacy isolation

- Separate legacy tests from canonical CI.
- Move legacy docs/frontend/Docker to `legacy/` (or a separate repo/branch).
- Drop `local_deep_research` from the built wheel (see
  `docs/LEGACY_MIGRATION_PLAN.md`).

## v0.3.0 — scientific depth

- Strengthen traceability/adjudication tooling and reviewer UX.
- Expand Article 1 corpus coverage (busca1 official guides; busca2a clinical
  guidelines/consensus/statements).
- Improve evidence-quality appraisal (`docs/NUTEV_EVIDENCE_QUALITY_APPRAISAL_PLAN.md`).

## Later

- busca2b (interventions/efficacy) as a separate corpus.
- Behavioral framework as a downstream product.
- Zenodo/OSF archival + DOI; reproducibility packaging.

### Deferred architectural refactors (parity-gated, phased)

These change scientific outputs if rushed, so each has its own phased,
parity-gated migration plan rather than a single rewrite:

- **Dissolve the `runtime_compat` shim layer** → `docs/REFACTOR_RUNTIME_COMPAT_MIGRATION.md`
  (move query terms, audit stage, synthesis defaults into the normal call graph).
- **Unify Global Watch with the search orchestrator** → `docs/REFACTOR_GLOBAL_WATCH_UNIFICATION.md`
  (shared dispatch/instrumentation; query-building unification is an explicit,
  measured decision, not an accidental change).

## Out of scope (for now)

- Git history rewrite.
- Presenting any automated output as a final clinical recommendation.

Track and discuss items via GitHub Issues (templates in `.github/ISSUE_TEMPLATE/`)
and Discussions.
