# NOTICE

This project, **NutEV/NutMEV** (`nutev-nutmev`), is built on top of an inherited
open-source engine and adds a distinct scientific/methodological layer. This
notice records provenance, licensing and the boundary between inherited code and
NutEV contributions, as required for a responsible public release.

## 1. Inherited project

- **Inherited engine:** Local Deep Research (LDR)
- **Original copyright:** Copyright (c) 2025 **LearningCircuit** (see `LICENSE`)
- **Original license:** MIT License (retained in `LICENSE`, unchanged)
- **Original project URL:** https://github.com/LearningCircuit/local-deep-research
  <!-- REVIEW REQUIRED: confirm the exact upstream repository URL and release/commit
       the inherited code was derived from before public release. -->

The inherited code lives under `src/local_deep_research/` and retains its MIT
license and copyright attribution. **That attribution must not be removed.**

## 2. Modifications

NutEV/NutMEV modifies and extends the inherited base by:

- adding a **canonical NutEV engine** under `src/nutev/` (analysis, audit, engine,
  export, global_watch, pipelines, protocol, querypacks, review, search, ui, api,
  demo, extract, download);
- adding NutEV rule/ontology/scoring/taxonomy configuration under `config/`;
- adding the canonical test suite `nutev_tests/`;
- adding NutEV methodology, governance and reproducibility documentation under
  `docs/`;
- decoupling package identity, entrypoints and dependencies from the inherited
  package (the `nutev` command and core no longer depend on LDR).

The inherited engine is being **isolated and progressively removed** from the
main distribution — see `docs/LEGACY_MIGRATION_PLAN.md`.

## 3. Boundary: inherited vs NutEV code

| Path | Provenance | License |
|---|---|---|
| `src/local_deep_research/**` | Inherited (LDR) | MIT (LearningCircuit) |
| `src/sitecustomize.py`, `src/usercustomize.py` | Inherited shims | MIT (LearningCircuit) |
| `tests/**` | Inherited (LDR) | MIT (LearningCircuit) |
| `src/nutev/**` | NutEV contribution | MIT (this repository) |
| `config/**`, `nutev_tests/**` | NutEV contribution | MIT (this repository) |
| NutEV `docs/**` (methodology/governance) | NutEV contribution | see doc headers |

## 4. NutEV authorship

- **NutEV/NutMEV contributions:** the NutEV/NutMEV Project.
  <!-- REVIEW REQUIRED: confirm the human author name(s), affiliation(s) and
       ORCID(s) for the NutEV contributions and record them in CITATION.cff.
       Do not invent this information. -->

## 5. Third-party dependencies and assets

- Python dependencies are declared in `pyproject.toml`; each carries its own
  upstream license. Optional/heavy stacks (Flask, SQLCipher, Elasticsearch,
  FAISS, LangChain, Playwright) are only pulled in via the `legacy`/optional
  extras.
- Bundled assets inherited from LDR (e.g. `src/local_deep_research/web/static`
  icons/fonts/favicon) may carry their own licenses.
  <!-- REVIEW REQUIRED: verify licenses of bundled fonts/icons/images before
       redistribution. -->

## 6. Open licensing / authorship questions (pending human/legal review)

1. Confirm exact upstream repository URL and derivation point (§1).
2. Confirm licenses of bundled binary assets (§5).
3. Confirm NutEV human authorship/affiliation/ORCID (§4) and mirror into
   `CITATION.cff`.
4. Confirm whether any part of the codebase needs a different license than MIT;
   if so, document per-part licensing here. Do not change the license on
   assumption.
