from pathlib import Path
from nutev.demo.demo_data import generate_demo_data
from nutev.ui.loaders import load_csv


def test_demo_data_generates_outputs(tmp_path: Path):
    generate_demo_data(tmp_path)
    required = [
        tmp_path/'02_metadata'/'metadata_master.csv',
        tmp_path/'02_metadata'/'NUTEV_EVIDENCE_CLAIMS.csv',
        tmp_path/'02_metadata'/'NUTEV_RECOMMENDATION_CANDIDATES.csv',
        tmp_path/'02_metadata'/'NUTEV_RECOMMENDATION_AUDIT_TRAIL.csv',
        tmp_path/'07_logs'/'run_summary.json',
    ]
    for p in required:
        assert p.exists()
    df, status = load_csv(tmp_path/'02_metadata'/'metadata_master.csv')
    assert status == 'ok' and len(df) >= 5 and bool(df['is_demo_data'].all())
