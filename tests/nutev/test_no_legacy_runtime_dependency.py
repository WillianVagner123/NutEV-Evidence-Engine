from pathlib import Path

from nutev.demo.demo_data import generate_demo_data
from nutev.ui.loaders import load_csv


def test_nutev_core_has_no_direct_local_deep_research_imports():
    base = Path('src/nutev')
    offenders = []
    for p in base.rglob('*.py'):
        text = p.read_text(encoding='utf-8', errors='ignore')
        if 'import local_deep_research' in text or 'from local_deep_research' in text:
            offenders.append(str(p))
    assert offenders == []


def test_demo_and_loaders_work_without_legacy_runtime(tmp_path: Path):
    generate_demo_data(tmp_path)
    df, status = load_csv(tmp_path / '02_metadata' / 'metadata_master.csv')
    assert status == 'ok'
    assert len(df) >= 5
