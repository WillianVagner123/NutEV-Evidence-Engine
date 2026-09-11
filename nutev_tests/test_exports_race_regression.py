"""Execute the production browser module with deterministic async ordering."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_superseded_export_load_cannot_erase_new_manifest_controls():
    result = subprocess.run(
        ['node', '--unhandled-rejections=strict', 'nutev_tests/fixtures/exports_race_test.cjs'],
        cwd=ROOT, capture_output=True, text=True, timeout=20, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'PASS: stale loads rejected' in result.stdout
