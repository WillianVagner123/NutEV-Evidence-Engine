# NutEV/NutMEV Validation Report

Date: 2026-05-25  
Branch: `nutev-upgrade-audit-pipeline`  
Target: `main`

## Scope

This report documents the validation plan and current validation checklist for the NutEV/NutMEV evidence engine used for doctoral qualification.

The system is intended to support a reproducible computational workflow for evidence identification, classification, auditing, and translation into **recommendation candidates** for the NutEV/NutMEV Dietary Protocol.

## Commands to run

```bash
python -m pip install -e ".[dashboard,platform]"
PYTHONPATH=src python -m pytest -q nutev_tests
nutev demo-data --project-root ./project_output_demo
nutev dashboard --project-root ./project_output_demo --port 8501
```

For a first controlled pilot:

```bash
PYTHONPATH=src NUTEV_DOWNLOAD_LIMIT=40 nutev --project-root ./project_output_pilot --workstreams busca1 --web-enabled
```

For the broader pilot:

```bash
PYTHONPATH=src nutev --project-root ./project_output_pilot --workstreams busca1 busca2a busca2b a3 --web-enabled
```

## Expected audit outputs

The pipeline should write the following files under `06_tables`:

- `NUTEV_EVIDENCE_CLAIMS.csv`
- `NUTEV_CLAIM_EVALUATIONS.csv`
- `NUTEV_CONFLICTS.csv`
- `NUTEV_RECOMMENDATION_CANDIDATES.csv`

## Expected final summary fields

The final `07_logs/run_summary.json` should include:

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

## Validation checklist

- [ ] `python -m pip install -e ".[dashboard,platform]"` completes on Python 3.12.
- [ ] `PYTHONPATH=src python -m pytest -q nutev_tests` runs successfully.
- [ ] `nutev demo-data --project-root ./project_output_demo` creates demo data.
- [ ] `nutev dashboard --project-root ./project_output_demo --port 8501` opens the dashboard.
- [ ] Pipeline execution does not fail at final summary because of undefined `claims`, `recommendations`, or `conflicts`.
- [ ] Audit CSV files are generated in `06_tables`.
- [ ] Recommendation candidates are never marked as final protocol recommendations.

## Known limitations

- External sources may fail because of network, SSL, API availability, publisher blocking, DOI redirects, or rate limits.
- External source failures should be treated as recoverable when possible.
- Download failures should be recorded in `failed_downloads.csv`.
- Extraction failures should be logged as events rather than hidden.
- Deterministic no-LLM extraction is conservative and requires human adjudication.

## Methodological note

The system supports evidence identification, classification, auditing, and candidate translation. It does not replace human review, risk-of-bias assessment, methodological adjudication, clinical interpretation, or final protocol decisions.

A `RecommendationCandidate` is **not** a final NutEV/NutMEV protocol recommendation. Any candidate requires documentary support, auditability, quality assessment, conflict adjudication, and explicit human review before protocol inclusion.

## Next steps

1. Integrate conservative claim extraction and recommendation candidate generation into `master_pipeline.py`.
2. Add unit tests for candidate generation, conflict handling, no automatic approval, artifact serialization, and demo/no-web pipeline execution.
3. Add dashboard views for claim review and candidate recommendation adjudication.
4. Re-run the validation checklist and record pass/fail results in this report.