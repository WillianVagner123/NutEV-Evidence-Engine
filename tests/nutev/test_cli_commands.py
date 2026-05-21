from pathlib import Path
import subprocess
import sys

from nutev.demo.demo_data import generate_demo_data
from nutev.export.pilot_report import generate_pilot_report


def test_demo_outputs_exist(tmp_path: Path):
    generate_demo_data(tmp_path)
    assert (tmp_path/'02_metadata'/'metadata_master.csv').exists()
    assert (tmp_path/'02_metadata'/'NUTEV_EVIDENCE_CLAIMS.csv').exists()
    assert (tmp_path/'02_metadata'/'NUTEV_RECOMMENDATION_CANDIDATES.csv').exists()
    assert (tmp_path/'07_logs'/'run_summary.json').exists()
    assert (tmp_path/'08_docs'/'NUTEV_METHODS_MASTER.md').exists()
    assert (tmp_path/'06_tables'/'NUTEV_HUMAN_REVIEW_QUEUE.xlsx').exists() or (tmp_path/'06_tables'/'NUTEV_HUMAN_REVIEW_QUEUE.csv').exists()


def test_cli_subcommands_help_mentions():
    out = subprocess.check_output([sys.executable, '-m', 'nutev.cli', '--help'], text=True)
    assert 'demo-data' in out
    assert 'dashboard' in out
    assert 'serve' in out
    assert 'pilot-report' in out


def test_readme_commands_exist():
    txt = Path('README.md').read_text(encoding='utf-8')
    for cmd in ['nutev demo-data', 'nutev dashboard', 'nutev serve', 'nutev global-watch']:
        assert cmd in txt


def test_pilot_report_generation(tmp_path: Path):
    generate_demo_data(tmp_path)
    out = generate_pilot_report(tmp_path)
    assert out.exists()
