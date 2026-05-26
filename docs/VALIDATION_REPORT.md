# NutEV/NutMEV Validation Report

Date: 2026-05-25
Branch: nutev-upgrade-audit-pipeline

## Scope

This report documents the validation plan for the NutEV/NutMEV evidence engine used for doctoral qualification.

## Commands to run

```bash
pip install -e ".[dashboard,platform]"
PYTHONPATH=src python -m pytest -q nutev_tests
nutev demo-data --project-root ./project_output_demo
nutev dashboard --project-root ./project_output_demo --port 8501
```

## Expected audit outputs

The pipeline should write the following files under `06_tables`:

- `NUTEV_EVIDENCE_CLAIMS.csv`
- `NUTEV_CLAIM_EVALUATIONS.csv`
- `NUTEV_CONFLICTS.csv`
- `NUTEV_RECOMMENDATION_CANDIDATES.csv`

## Methodological note

The system supports evidence identification, classification, auditing, and candidate translation. It does not replace human review, methodological adjudication, or final protocol decisions.
