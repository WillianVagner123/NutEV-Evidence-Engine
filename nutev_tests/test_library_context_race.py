from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_library_controls_and_async_scope_are_fail_closed():
    result = subprocess.run(['node', '--unhandled-rejections=strict', 'nutev_tests/fixtures/library_context_race.cjs'], cwd=ROOT, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'PASS: initialization guarded' in result.stdout


def test_browser_requires_resolved_fulltext_and_project_scope():
    script = (ROOT/'tools/run_pilot_browser_closeout.py').read_text()
    assert "to_have_text('Nenhum acesso ativo a texto completo neste contexto.')" in script
    assert "to_have_text('projeto atual')" in script
    html = (ROOT/'apps/nutev-web/evidence-library.html').read_text()
    assert 'id="libraryScope" disabled' in html
    assert 'id="saveLibraryPlacement" type="button" disabled' in html
