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


def test_nutev_workflows_use_ci_requirements_manifest():
    tests_workflow = Path(".github/workflows/nutev-tests.yml").read_text(encoding="utf-8")
    smoke_workflow = Path(".github/workflows/nutev-smoke.yml").read_text(encoding="utf-8")
    assert "requirements/nutev-ci.txt" in tests_workflow
    assert "requirements/nutev-ci.txt" in smoke_workflow
    assert "pip install --no-deps -e ." in tests_workflow
    assert "pip install --no-deps -e ." in smoke_workflow


def test_nutev_workflows_use_node24_compatible_actions():
    tests_workflow = Path(".github/workflows/nutev-tests.yml").read_text(encoding="utf-8")
    smoke_workflow = Path(".github/workflows/nutev-smoke.yml").read_text(encoding="utf-8")
    assert "actions/github-script@v8" in tests_workflow
    assert "actions/checkout@v5" in tests_workflow
    assert "actions/setup-python@v6" in tests_workflow
    assert "actions/checkout@v5" in smoke_workflow
    assert "actions/setup-python@v6" in smoke_workflow
