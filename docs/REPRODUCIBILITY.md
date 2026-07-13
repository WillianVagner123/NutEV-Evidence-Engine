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
- **Traceability:** every claim links to a source document + locator
  (`docs/SCIENTIFIC_GOVERNANCE.md`).
- **Run artifacts:** logs and run summaries under `07_logs/`, structured tables
  under `06_tables/`, manifests describing what was produced.
- **No hidden state:** no LLM is required; when enabled, its role is logged.

## Reproducing the Article 1 pilot

See `examples/article1_pilot/` for a small, self-contained, key-free example with
its configuration, queries, extraction schema, synthetic/public-metadata inputs
and clearly-labeled demonstration results.

## Versioning

- Software: semantic versioning + `CHANGELOG.md`.
- Methodology: `docs/CHANGELOG_METODOLOGICO.md`.
- Releases: `docs/RELEASE_GUIDE.md` / release checklist; first public tag
  `v0.1.0-alpha`.

## Known environment caveats

- Optional `documents` extra needs system `tesseract` and `poppler`.
- The legacy stack (`[legacy]`) is not needed for canonical reproduction.
