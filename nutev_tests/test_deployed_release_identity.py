"""Build labels must distinguish semantic package version from the commit SHA."""
from pathlib import Path
import subprocess

from nutev.__version__ import __version__

ROOT = Path(__file__).resolve().parents[1]


def test_deploy_reads_the_package_version_not_short_sha():
    text = (ROOT / '.github/workflows/deploy-hetzner.yml').read_text()
    line = next(line.strip() for line in text.splitlines() if line.strip().startswith('VERSION='))
    command = 'TARGET_SHA=' + 'a' * 40 + '\n' + line + '\nprintf "%s" "$VERSION"'
    result = subprocess.run(['bash', '-euc', command], cwd=ROOT, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert result.stdout == __version__


def test_http_release_version_mismatch_cannot_pass():
    from tools.check_runtime_http_surface import EXPECTED_PROVIDER_IDS, validate_runtime_payloads
    providers = {'providers': [{'id': name, 'label': name} for name in EXPECTED_PROVIDER_IDS]}
    for version in ({'commit': 'x'}, {'commit': 'x', 'version': 'wrong'}):
        errors = validate_runtime_payloads(health={'status': 'ok'}, version=version,
            providers=providers, expected_commit='x', expected_version=__version__)
        assert 'version.version mismatch with expected package version' in errors
    assert validate_runtime_payloads(health={'status': 'ok'},
        version={'commit': 'x', 'version': __version__}, providers=providers,
        expected_commit='x', expected_version=__version__) == []


def test_recovery_harness_executes_actual_workflow_functions():
    script = (ROOT / 'tools/rehearse_release_recovery.sh').read_text()
    assert "text=Path('.github/workflows/deploy-hetzner.yml').read_text()" in script
    assert 'recover_on_error' in script and 'rollback; rollback' in script
    assert 'OLD_STOPPED=1; PROMOTED=0' in script
    assert 'raise SystemExit(23)' in script
    assert 'synthetic_data_preserved' in script
    assert 'bash tools/rehearse_release_recovery.sh' in (ROOT / 'tools/run_container_release_gate.sh').read_text()
    result = subprocess.run(['bash', '-n', 'tools/rehearse_release_recovery.sh'], cwd=ROOT, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
