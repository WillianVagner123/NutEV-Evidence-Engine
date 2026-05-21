from __future__ import annotations

from pathlib import Path
import json

import pandas as pd

from nutev.ui.loaders import calculate_overview_metrics, load_csv, load_json_file, load_xlsx_or_csv


def test_loader_missing_file_returns_empty(tmp_path: Path):
    df, status = load_csv(tmp_path / 'missing.csv')
    assert df.empty
    assert 'not available yet' in status


def test_loader_csv(tmp_path: Path):
    p = tmp_path / 'a.csv'
    pd.DataFrame([{'x': 1}]).to_csv(p, index=False)
    df, status = load_csv(p)
    assert status == 'ok'
    assert len(df) == 1


def test_loader_xlsx_if_available(tmp_path: Path):
    px = tmp_path / 'a.xlsx'
    try:
        pd.DataFrame([{'x': 2}]).to_excel(px, index=False)
    except Exception:
        return
    df, status = load_xlsx_or_csv(px)
    assert status == 'ok'
    assert len(df) == 1


def test_run_summary_read(tmp_path: Path):
    p = tmp_path / 'run_summary.json'
    p.write_text(json.dumps({'records': 3}), encoding='utf-8')
    data, status = load_json_file(p)
    assert status == 'ok'
    assert data['records'] == 3


def test_metrics_calculated_without_inventing_fields():
    m = calculate_overview_metrics({}, pd.DataFrame([{'download_status': 'pdf', 'extraction_status': 'ok'}]), pd.DataFrame([{'claim_status': 'supported', 'needs_human_review': False}]), pd.DataFrame([{'recommendation_status': 'ready_for_human_review'}]))
    assert m['total_records'] == 1
    assert m['evidence_claims_total'] == 1
    assert 'unknown_field' not in m


def test_xlsx_csv_fallback_empty_with_warning(tmp_path: Path):
    df, status = load_xlsx_or_csv(tmp_path / 'none.xlsx', tmp_path / 'none.csv')
    assert df.empty
    assert 'not available yet' in status
