# Reproducibility

NutEV/NutMEV is designed so that a person with no API keys and no protected data
can reproduce a demonstration of the full pipeline shape, and so that scientific
runs are traceable and versioned.

## Zero-key demonstration

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
python -m pip install -e ".[dashboard]"
nutev demo-data   --project-root ./project_output_demo
nutev dashboard   --project-root ./project_output_demo
```

This runs without OpenAI, Google, SerpAPI, Brave, real data or protected PDFs.
It produces synthetic metadata, scored tables and reports under
`project_output_demo/` (clearly demo, **not** evidence).

## What makes a run reproducible

- **Pinned environment:** core deps in `requirements/nutev-core.txt`; CI profile
  in `requirements/nutev-ci.txt`; Python 3.12.
- **Deterministic config:** rules/ontology/scoring/taxonomy under `config/` are
  versioned; methodology changes are recorded (`docs/CHANGELOG_METODOLOGICO.md`).
- **Config digest:** each run records exactly which config it used (see
  *Config provenance* below), so a result can be tied back to its configuration.
- **Traceability:** every claim links to a source document + locator
  (`docs/SCIENTIFIC_GOVERNANCE.md`).
- **Run artifacts:** logs and run summaries under `07_logs/`, structured tables
  under `06_tables/`, manifests describing what was produced.
- **No hidden state:** no LLM is required; when enabled, its role is logged.

## Config provenance (`config_digest`)

Taxonomy and scoring configs are assembled by deep-merging a base file under
`config/` (e.g. `keyword_taxonomy.json`) with any sibling
`*_supplement*.json` layers. Supplements are applied in a fixed order — the
exact `_supplement` file first, then each `_supplement_*` variant sorted by
name — so the merge is deterministic. Adding, editing or removing a supplement
therefore changes the effective configuration.

To keep that auditable, every pipeline run writes `07_logs/config_provenance.json`
and stamps a `config_digest` into `07_logs/search_job_snapshot.json`. The record
lists, per config family, each source file in merge order with its own SHA-256,
the SHA-256 of the fully merged config, and one overall `config_digest` that
changes iff any merged config changed.

- **Same inputs → same digest:** two runs sharing a `config_digest` used
  identical taxonomy/scoring.
- **Digest moved → configuration moved:** cite the `config_digest` alongside the
  software version and `CHANGELOG_METODOLOGICO.md` entry when reporting results.

The digest is provenance only — recording it never alters what is merged, so it
cannot change a run's scientific output.

## Reproducing the Article 1 pilot

See `examples/article1_pilot/` for a small, self-contained, key-free example with
its configuration, queries, extraction schema, synthetic/public-metadata inputs
and clearly-labeled demonstration results.

## Versioning

- Software: semantic versioning + `CHANGELOG.md`.
- Methodology: `docs/CHANGELOG_METODOLOGICO.md`.
- Release process: `docs/RELEASE_CHECKLIST.md`; first public tag `v0.1.0-alpha`.

## Known environment caveats

- Optional `documents` extra needs system `tesseract` and `poppler`.
- The legacy stack (`[legacy]`) is not needed for canonical reproduction.
