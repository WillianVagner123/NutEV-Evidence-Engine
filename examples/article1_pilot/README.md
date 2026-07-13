# Article 1 — reproducible pilot (demonstration)

**Article 1:** *"Domínios da Nutrição do Estilo de Vida em guias alimentares e
diretrizes clínicas: revisão de escopo e análise documental para subsidiar o
Protocolo NutEV."*

This folder is a small, **self-contained, key-free** demonstration of the Article 1
workflow. It contains only: configuration, queries, an extraction schema, synthetic
/public-metadata inputs, instructions, and small results **clearly labeled as
demonstration**.

> ⚠️ This is a **demonstration**, not scientific evidence. It uses synthetic rows
> and public metadata (DOI/official URLs) only. **No third-party PDFs or protected
> full texts are included** (see `docs/COPYRIGHT_AND_FULL_TEXT_POLICY.md`).

## Corpora (Article 1 scope)

- `busca1` — official dietary guides.
- `busca2a` — clinical guidelines, consensus and statements.
- `busca2b` — interventions/efficacy (**outside** the Article 1 core corpus).
- behavioral framework — a **later** product.

## Files

| File | Purpose |
|---|---|
| `config.json` | pilot configuration (scope, workstreams, no network/LLM) |
| `queries.json` | example queries for `busca1` and `busca2a` |
| `extraction_schema.json` | fields extracted per document (with source locator) |
| `demo_data/metadata_sample.csv` | synthetic/public **metadata only** (no full text) |
| `demo_data/expected_domains.json` | small illustrative result (demonstration) |

## Run the key-free demonstration

```bash
python -m pip install -e ".[dashboard]"
nutev demo-data --project-root ./project_output_article1_demo
nutev dashboard --project-root ./project_output_article1_demo
```

`nutev demo-data` generates the synthetic pipeline outputs (metadata, scored tables,
logs, reports). Open the dashboard to inspect the evidence matrices and the human
review queue. Nothing here requires OpenAI, Google, SerpAPI, Brave or real data.

## What a real (non-demo) run would add

A real Article 1 run would populate `busca1`/`busca2a` from official sources at
runtime (into git-ignored `project_output*/03_corpus/`), never committing protected
documents. Only metadata, sanitized logs, derived tables and permitted reports are
shareable. Final domain classification always requires human review.
