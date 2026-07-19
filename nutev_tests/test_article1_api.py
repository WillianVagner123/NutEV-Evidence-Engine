"""Article-1 web API (§15) — endpoints over the pipeline outputs (needs fastapi)."""
from __future__ import annotations

from pathlib import Path

import pytest


def _project_with_outputs(tmp_path: Path) -> Path:
    from nutev.export.metadata_tables import write_simple_csv

    (tmp_path / "06_tables").mkdir(parents=True, exist_ok=True)
    (tmp_path / "07_logs").mkdir(parents=True, exist_ok=True)
    write_simple_csv(
        [{"name": "denominator", "unit": "file", "n": 3, "note": "x"}],
        tmp_path / "07_logs" / "denominator_registry.csv",
    )
    (tmp_path / "07_logs" / "prisma_counts.json").write_text(
        '{"identified_file_assets": 3, "unique_document_versions": 2, "document_families": 1,'
        ' "ready_to_screen": 2, "excluded_no_full_text_or_poor_ocr": 1, "included": "pending", "note": "x"}',
        encoding="utf-8",
    )
    write_simple_csv(
        [{"name": "Guia", "country": "brazil", "A_state": "RECOMMENDED", "B_state": "OPERATIONALIZED",
          "C_state": "MENTIONED", "D_state": "NOT_ASSESSED", "n_domains_positive": 2}],
        tmp_path / "06_tables" / "NUTEV_GUIDES_ABCD_MATRIX.csv",
    )
    write_simple_csv(
        [{"rank": 1, "name": "Guia", "country": "brazil", "gem_score": 12,
          "domains_covered": "ABCD", "manuscript_section": "results"}],
        tmp_path / "06_tables" / "NUTEV_GUIDES_EVIDENCE_GEMS.csv",
    )
    write_simple_csv(
        [{"name": "Guia", "domain": "A", "state": "RECOMMENDED", "screen_flag": "ready_to_screen"}],
        tmp_path / "06_tables" / "NUTEV_GUIDES_DOMAIN_STATES.csv",
    )
    write_simple_csv(
        [{"name": "Guia", "screen_flag": "ready_to_screen", "export_ready": False}],
        tmp_path / "06_tables" / "NUTEV_GUIDES_SCREENING_QUEUE.csv",
    )
    return tmp_path


def _client(tmp_path: Path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from nutev.api.server import create_app

    return TestClient(create_app(_project_with_outputs(tmp_path)))


def test_denominators_and_prisma(tmp_path):
    c = _client(tmp_path)
    den = c.get("/api/article1/denominators").json()
    assert den["items"][0]["n"] == 3
    prisma = c.get("/api/article1/prisma").json()
    assert prisma["included"] == "pending"          # never a final corpus


def test_abcd_matrix_and_gems_carry_warnings(tmp_path):
    c = _client(tmp_path)
    m = c.get("/api/article1/abcd-matrix").json()
    assert m["items"][0]["A_state"] == "RECOMMENDED"
    assert "assistiva" in m["note"].lower()
    g = c.get("/api/article1/gems").json()
    assert g["items"][0]["gem_score"] == 12
    assert "descritivo" in g["note"].lower()        # not risk-of-bias


def test_domain_states_filter_and_dashboard(tmp_path):
    c = _client(tmp_path)
    ds = c.get("/api/article1/domain-states?state=RECOMMENDED").json()
    assert all(r["state"] == "RECOMMENDED" for r in ds["items"])
    html = c.get("/api/article1/dashboard")
    assert html.status_code == 200 and "Artigo 1" in html.text
