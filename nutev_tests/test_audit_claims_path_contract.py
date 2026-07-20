"""Path contract: a real run's claims/recommendations must land where the UI reads.

The audit stage (claims, evaluations, conflicts, recommendation candidates) is
injected by ``runtime_compat`` wrapping ``curate_outputs``. It previously wrote
those CSVs to ``06_tables/`` while every reader — the Streamlit dashboard, the
FastAPI routes, the pilot report and the Export Center — reads them from
``02_metadata/``. The result was that after a real ``run_pipeline`` the
evidence/recommendation panels rendered empty. This test pins the contract so the
write location can never drift away from the read location again.
"""
from __future__ import annotations

from pathlib import Path

from nutev.export.curation import curate_outputs
from nutev.export.curation_finalize import finalize_curated_layer

# The canonical read locations, taken from the actual reader modules.
DASHBOARD_CLAIMS = "02_metadata/NUTEV_EVIDENCE_CLAIMS.csv"          # ui/dashboard.py:41
DASHBOARD_RECS = "02_metadata/NUTEV_RECOMMENDATION_CANDIDATES.csv"  # ui/dashboard.py:42


def _run_curation(project_root: Path) -> dict:
    """Run curation + the first-class finalization exactly as the pipeline does."""
    curated_dir = project_root / "10_curated"
    for sub in ("02_metadata", "06_tables", "07_logs", curated_dir.name):
        (project_root / sub).mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "document_id": "doc_1",
            "title": "Clinical guideline should encourage vegetables for obesity care.",
            "abstract": "The guideline should encourage vegetables for adults with obesity.",
            "extracted_text": "The guideline should encourage vegetables for adults with obesity.",
            "source_provider": "pubmed",
            "source_type": "clinical_guideline",
            "clinical_conditions": ["obesity"],
            "diet_patterns": ["plant_forward"],
            "outcomes": ["weight_management"],
            "workstream": "busca1",
        }
    ]
    summary = curate_outputs(rows, curated_dir)
    finalize_curated_layer(rows, curated_dir, summary)
    return summary


def test_real_run_writes_claims_where_the_dashboard_reads(tmp_path: Path):
    summary = _run_curation(tmp_path)

    # The audit stage actually produced claims/recommendations...
    assert summary.get("evidence_claims_total", 0) >= 1
    assert summary.get("recommendation_candidates_total", 0) >= 1

    # ...and they are in 02_metadata (the read location), not stranded in 06_tables.
    assert (tmp_path / DASHBOARD_CLAIMS).exists(), "claims not written where the dashboard reads"
    assert (tmp_path / DASHBOARD_RECS).exists(), "recommendations not written where the dashboard reads"


def test_dashboard_loader_actually_finds_the_claims(tmp_path: Path):
    import pytest

    pytest.importorskip("streamlit")  # dashboard module imports streamlit at top
    # Exercise the real reader, not just the path, so a loader change is caught too.
    _run_curation(tmp_path)
    from nutev.ui.dashboard import load_data

    data = load_data(tmp_path)
    claims = data["claims"]
    assert claims is not None and len(claims) >= 1
    # The derived matrices (C3) also reach the dashboard now, not just claims.
    assert (tmp_path / "06_tables" / "NUTEV_EVIDENCE_CONVERGENCE_MATRIX.xlsx").exists()
    assert (tmp_path / "06_tables" / "NUTEV_PROTOCOL_READINESS_MATRIX.xlsx").exists()
