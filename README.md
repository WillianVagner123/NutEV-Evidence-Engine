# NutEV/NutMEV — Evidence Engine for Lifestyle Nutrition

Pipeline computacional reprodutível para identificação, classificação, auditoria e tradução de evidências em **recomendações candidatas** para o Protocolo Dietético NutEV/NutMEV.

> **Regra metodológica central:** uma `RecommendationCandidate` não é recomendação final do protocolo. Toda candidata exige revisão humana, adjudicação metodológica e vínculo documental antes de qualquer uso como recomendação NutEV/NutMEV.

## Visão geral

O projeto organiza uma arquitetura científica local para apoiar a qualificação de doutorado e o desenvolvimento do Protocolo Dietético NutEV/NutMEV. Ele inclui:

- CLI principal `nutev`;
- dashboard local;
- API local;
- demo data;
- pipeline de busca, classificação, download e extração;
- Global Watch;
- Audit Engine;
- Scientific Rigor Layer;
- Human Review and Adjudication.

## Runtime canônico e legado

A arquitetura canônica para o NutEV/NutMEV está em:

```text
src/nutev
```

O repositório evoluiu a partir de uma base histórica `local-deep-research`. Diretórios e imports legados não devem ser removidos de forma brusca enquanto ainda houver dependências ativas. Para novos módulos científicos NutEV/NutMEV, prefira `src/nutev`.

## Instalação rápida

### Windows PowerShell

```powershell
git clone https://github.com/WillianVagner123/NUT-MEV_NEW.git
cd NUT-MEV_NEW
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dashboard,platform]"
```

### macOS/Linux

```bash
git clone https://github.com/WillianVagner123/NUT-MEV_NEW.git
cd NUT-MEV_NEW
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dashboard,platform]"
```

O projeto requer Python `>=3.12,<3.15`.

## Demo

```bash
nutev demo-data --project-root ./project_output_demo
nutev dashboard --project-root ./project_output_demo --port 8501
```

Depois acesse:

```text
http://127.0.0.1:8501
```

API local:

```bash
nutev serve --project-root ./project_output_demo --host 127.0.0.1 --port 8000
```

URLs:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`

## Primeiro piloto real

```bash
nutev --project-root ./project_output_pilot --workstreams busca1 busca2a busca2b a3 --web-enabled
nutev pilot-report --project-root ./project_output_pilot
nutev dashboard --project-root ./project_output_pilot --port 8501
```

Variáveis úteis para integrações bibliográficas:

```bash
export NCBI_EMAIL="seu-email@exemplo.com"
export NCBI_API_KEY="sua-chave-ncbi"
export CROSSREF_MAILTO="seu-email@exemplo.com"
export OPENALEX_MAILTO="seu-email@exemplo.com"
```

Nunca coloque chaves de API no GitHub, em logs ou em outputs científicos.

## Outputs esperados

Camadas principais em `project_output_*`:

- `06_tables`: matrizes, PRISMA, tabelas e artefatos de auditoria;
- `07_logs`: eventos, snapshots, resumo da execução e rastreabilidade;
- `10_curated`: metadados curados, documentos únicos e documentos operacionais priorizados.

Artefatos de auditoria esperados em `06_tables`:

- `NUTEV_EVIDENCE_CLAIMS.csv`
- `NUTEV_CLAIM_EVALUATIONS.csv`
- `NUTEV_CONFLICTS.csv`
- `NUTEV_RECOMMENDATION_CANDIDATES.csv`

Resumo final esperado em `07_logs/run_summary.json`:

- `records`
- `downloads_ok`
- `downloads_failed`
- `ocr_docs`
- `curated_unique_documents`
- `evidence_claims_total`
- `evidence_claims_supported`
- `evidence_claims_needs_review`
- `recommendation_candidates_total`
- `recommendation_candidates_ready_review`
- `recommendation_candidates_insufficient_evidence`
- `conflicting_evidence_total`

## Testes NutEV

Caminho padronizado:

```bash
PYTHONPATH=src python -m pytest -q nutev_tests
```

No Windows PowerShell:

```powershell
$env:PYTHONPATH="src"
python -m pytest -q nutev_tests
```

## Limitações metodológicas

O sistema apoia identificação, classificação, auditoria e tradução preliminar de evidências. Ele **não substitui** revisão sistemática humana, avaliação de risco de viés, dupla checagem, adjudicação de conflitos, interpretação clínica ou decisão final do protocolo.

Recomendações candidatas podem receber estados como:

- `ready_for_human_review`
- `conflicting_evidence`
- `draft_needs_evidence`
- `insufficient_evidence`

Nenhum desses estados equivale a recomendação final.

## Documentação

- [`docs/RUN_LOCAL.md`](docs/RUN_LOCAL.md)
- [`docs/VALIDATION_REPORT.md`](docs/VALIDATION_REPORT.md)
- [`docs/NUTEV_AUDIT_ENGINE.md`](docs/NUTEV_AUDIT_ENGINE.md)
- [`docs/NUTEV_CONTROL_CENTER.md`](docs/NUTEV_CONTROL_CENTER.md)
- [`docs/NUTEV_EVIDENCE_TO_PROTOCOL_FLOW.md`](docs/NUTEV_EVIDENCE_TO_PROTOCOL_FLOW.md)
- [`docs/NUTEV_PLATFORM_API.md`](docs/NUTEV_PLATFORM_API.md)
- [`docs/NUTEV_PROVIDER_SETTINGS.md`](docs/NUTEV_PROVIDER_SETTINGS.md)
- [`docs/REPOSITORY_STRUCTURE.md`](docs/REPOSITORY_STRUCTURE.md)
- [`docs/LEGACY_CLEANUP_AUDIT.md`](docs/LEGACY_CLEANUP_AUDIT.md)
- [`docs/LEGACY_DEPENDENCY_MAP.md`](docs/LEGACY_DEPENDENCY_MAP.md)

## Revisão humana

As decisões humanas são persistidas em `project_output/07_logs/human_review_decisions.csv` quando o fluxo de revisão está habilitado. Nenhuma recomendação deve ser considerada final sem revisão humana explícita, lastro documental e adjudicação metodológica.
## NutEV/NutMEV robust search runtime

The canonical runtime is `src/nutev`. The older `src/local_deep_research` package remains only as legacy/reference code and is not the main runtime.

Scientific search does not depend on Google. PubMed, Europe PMC, OpenAlex, Crossref and official sources run through safe provider handling; provider failures are logged and the pipeline exports partial results instead of crashing. PubMed uses NCBI E-utilities with `usehistory=y`, `WebEnv`, `query_key`, paginated batches, retry/backoff and checkpoints under `07_logs/checkpoints/pubmed/`.

Configure local environment variables from `.env.example`. The most important PubMed settings are `NCBI_EMAIL`, optional `NCBI_API_KEY`, and `NCBI_TOOL=nutev_pipeline`. Google/SerpAPI keys are optional and are used only for gray-literature discovery.

More details: `docs/SEARCH_PROVIDERS.md` and `docs/PUBMED_TROUBLESHOOTING.md`.

## Scientific databases

The pipeline queries the following databases by default (all free; no credential
required to run), each through the orchestrator's retry/checkpoint/failure-logging
contract:

- **PubMed/MEDLINE** (NCBI E-utilities, history server, checkpoints)
- **Europe PMC**
- **OpenAlex**
- **Crossref**
- **Semantic Scholar** (Graph API; optional `SEMANTIC_SCHOLAR_API_KEY` for higher rate limits)
- **DOAJ** (Directory of Open Access Journals)
- **SciELO** (Latin American, via Crossref prefix `10.1590`)
- **Preprints** (medRxiv/bioRxiv and others, via Europe PMC `SRC:PPR`)
- **ClinicalTrials.gov** (API v2 trial registry)
- **CORE** (open-access aggregator) — optional, enabled with a free `CORE_API_KEY`

Provider failures are logged to `07_logs/provider_failures.csv` and the pipeline
exports partial results instead of crashing.

## Open-access full-text downloading

To maximize how many full texts are retrieved, the downloader prefers a
discoverable open-access PDF before the generic resolver, in order: a provider's
`oa_pdf_url` → **Unpaywall** (by DOI, requires `UNPAYWALL_EMAIL`) → **PMC** (by
PMCID). Publisher pages are scraped for PDF links (meta tags, `<link>`/anchor
hints, `meta refresh`) across common publisher URL patterns.

## QUALIS A1 methodological outputs

Each run also emits publication-grade reporting scaffolding (these are
scaffolding for the human researcher; they do not replace screening, appraisal
or adjudication):

- `06_tables/NUTEV_PRISMA2020_FLOW.csv` — PRISMA 2020 flow with per-database
  identified counts plus dedup/screening/full-text/claims stages;
- `08_docs/NUTEV_SEARCH_STRATEGY_APPENDIX.md` — the exact queries executed per
  database per workstream (PRISMA 2020 item 7, reproducible search);
- `08_docs/NUTEV_PROSPERO_PROTOCOL.md` and `08_docs/NUTEV_PRISMA2020_CHECKLIST.md`
  — protocol registration template and the 27-item checklist;
- `06_tables/NUTEV_RISK_OF_BIAS.csv` (+ guide) — RoB 2 / ROBINS-I / AMSTAR 2
  domain template, one row per full-text document;
- `06_tables/NUTEV_REPRODUCIBILITY.json` — run dates, package version,
  per-database record counts, total queries and SHA-256 hashes of the
  configuration that drove the run.
