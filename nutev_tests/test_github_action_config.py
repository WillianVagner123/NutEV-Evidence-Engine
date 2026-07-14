from pathlib import Path


def test_workflow_exists():
    assert Path(".github/workflows/nutev-global-watch.yml").exists()


def test_workflow_has_webhook_env():
    txt = Path(".github/workflows/nutev-global-watch.yml").read_text(encoding="utf-8")
    assert "NUTEV_DIGEST_WEBHOOK_URL" in txt


def test_nutev_ci_requirements_exists():
    txt = Path("requirements/nutev-ci.txt").read_text(encoding="utf-8")
    assert "pydantic" in txt
    assert "pytest" in txt


def test_ci_workflow_uses_ci_requirements_manifest():
    # The canonical CI gate (ci.yml) installs deps from the CI manifest and the
    # project with --no-deps, then runs the full nutev_tests suite.
    ci_workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "requirements/nutev-ci.txt" in ci_workflow
    assert "pip install --no-deps -e ." in ci_workflow
    assert "pytest -q nutev_tests" in ci_workflow


def test_ci_workflow_uses_node24_compatible_actions():
    ci_workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "actions/checkout@v5" in ci_workflow
    assert "actions/setup-python@v6" in ci_workflow
