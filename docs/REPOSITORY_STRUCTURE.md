# Repository Structure (NutEV Canonical)

## Canonical runtime

Use this namespace for current NutEV/NutMEV scientific work:

- `src/nutev/`
  - `audit/`: claim extraction, claim evaluation, conflict detection, candidate recommendation models;
  - `analysis/`: classification, relevance scoring, PRISMA, synthesis helpers;
  - `demo/`: simulated demo data for dashboard and qualification demonstration;
  - `engine/`: run IDs, events, artifacts, job snapshots;
  - `export/`: tables, logs, Rayyan exports, methods text, curation outputs;
  - `global_watch/`: monitoring and watch workflows;
  - `pipelines/`: main pipeline orchestration;
  - `querypacks/`: query generation and provider-specific query rendering;
  - `review/`: human review and adjudication support;
  - `search/`: PubMed, Europe PMC, OpenAlex, Crossref and official source connectors;
  - `ui/`: dashboard/control-center components;
  - `cli.py`, `settings.py`.

## Configs

- `config/`
  - `audit_rules.json`
  - `evidence_lenses.json`
  - `nutev_ontology.json`
  - `recommendation_rules.json`
  - `source_registry.json`
  - `keyword_taxonomy.json`
  - `scoring_rules.json`
  - `official_sources_manifest.json`

## Docs metodológicos

- `docs/NUTEV_AUDIT_ENGINE.md`
- `docs/NUTEV_CONTROL_CENTER.md`
- `docs/NUTEV_EVIDENCE_TO_PROTOCOL_FLOW.md`
- `docs/CHANGELOG_METODOLOGICO.md`
- `docs/VALIDATION_REPORT.md`
- `docs/LEGACY_CLEANUP_AUDIT.md`
- `docs/LEGACY_DEPENDENCY_MAP.md`

## Testes NutEV

Caminho padronizado:

- `nutev_tests/`

Comando:

```bash
PYTHONPATH=src python -m pytest -q nutev_tests
```

## Outputs locais

- Default local output root: `project_output/`
- Demo output root: `project_output_demo/`
- Pilot output root: `project_output_pilot/`

Pastas esperadas:

- `06_tables/`: matrizes, PRISMA e artefatos de auditoria;
- `07_logs/`: logs, eventos, snapshots e resumo final;
- `10_curated/`: metadados curados e documentos únicos.

## Legacy area

- `src/local_deep_research/` e documentos/workflows associados permanecem no repositório por compatibilidade.
- Não remover diretórios legados sem checar imports ativos.
- Novos módulos de pesquisa NutEV/NutMEV devem ser criados em `src/nutev/`.

## Run demo

```bash
nutev demo-data --project-root ./project_output_demo
nutev dashboard --project-root ./project_output_demo --port 8501
```

## Run pilot

```bash
nutev --project-root ./project_output_pilot --workstreams busca1 busca2a busca2b a3 --web-enabled
```

## Methodological guardrail

`RecommendationCandidate` é candidata à recomendação, não recomendação final. A inclusão no protocolo requer revisão humana, adjudicação de conflitos e lastro documental auditável.

## Canonical and legacy search layers

- `src/nutev/`: canonical NutEV/NutMEV runtime, including CLI, pipelines, provider orchestration, checkpoints, exports and Global Watch.
- `src/nutev/search/`: robust provider layer for PubMed, Europe PMC, OpenAlex, Crossref, optional Google/SerpAPI stubs, provider orchestration and checkpoints.
- `src/local_deep_research/`: legacy/reference implementation retained for comparison only; do not switch the runtime back to this package.
