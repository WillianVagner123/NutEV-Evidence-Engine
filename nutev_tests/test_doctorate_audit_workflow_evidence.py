from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'production-doctorate-audit.yml'


def test_doctorate_audit_preserves_sanitized_report_on_failure():
    text = WORKFLOW.read_text(encoding='utf-8')
    assert "set +e" in text
    assert "AUDIT_EXIT=$?" in text
    assert "if [[ ! -s doctorate-runtime.json ]]" in text
    assert "remote_audit_command_failed_without_report" in text
    assert "if: always()" in text
    assert "path: doctorate-runtime.json" in text


def test_doctorate_audit_still_fails_when_runtime_report_is_not_pass():
    text = WORKFLOW.read_text(encoding='utf-8')
    assert "data.get('read_only') is True" in text
    assert "data.get('scientific_state_modified') is False" in text
    assert "data.get('legacy_binding_performed') is False" in text
    assert "data.get('search_executed') is False" in text
    assert "if audit_exit != 0 or data.get('status') != 'PASS':" in text
    assert "raise SystemExit(1)" in text
