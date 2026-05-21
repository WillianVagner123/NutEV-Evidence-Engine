# Repository Structure (NutEV Canonical)

## Canonical runtime
- `src/nutev/`
  - `audit/`, `analysis/`, `demo/`, `engine/`, `export/`, `global_watch/`, `pipelines/`, `querypacks/`, `review/`, `search/`, `ui/`, `cli.py`, `settings.py`.

## Configs
- `config/`
  - `audit_rules.json`, `evidence_lenses.json`, `nutev_ontology.json`, `recommendation_rules.json`, `source_registry.json`, `keyword_taxonomy.json`, `scoring_rules.json`, `official_sources_manifest.json`.

## Docs metodológicos
- `docs/NUTEV_AUDIT_ENGINE.md`
- `docs/NUTEV_CONTROL_CENTER.md`
- `docs/NUTEV_EVIDENCE_TO_PROTOCOL_FLOW.md`
- `docs/CHANGELOG_METODOLOGICO.md`
- `docs/LEGACY_CLEANUP_AUDIT.md`
- `docs/LEGACY_DEPENDENCY_MAP.md`

## Testes NutEV
- `tests/nutev/`

## Outputs
- Default local output root: `project_output/`
- Demo output root: `project_output_demo/`

## Legacy area
- `src/local_deep_research/` and associated legacy docs/workflows remain in repository for compatibility, but are not canonical for NutEV runtime.

## Run demo
```bash
nutev demo-data --project-root ./project_output_demo
```

## Run tests (NutEV scope)
```bash
PYTHONPATH=src python -m pytest -q tests/nutev
```
