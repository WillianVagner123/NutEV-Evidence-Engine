from pathlib import Path

WORKFLOW = Path(".github/workflows/nutev-ci.yml")


def test_ci_workflow_exists():
    assert WORKFLOW.exists()


def test_nutev_ci_requirements_exists():
    txt = Path("requirements/nutev-ci.txt").read_text(encoding="utf-8")
    assert "pydantic" in txt
    assert "pytest" in txt


def test_ci_workflow_runs_lint_and_tests():
    txt = WORKFLOW.read_text(encoding="utf-8")
    assert "ruff check" in txt
    assert "pytest" in txt
    assert "requirements/nutev-ci.txt" in txt
    assert "pip install --no-deps -e ." in txt


def test_ci_workflow_uses_compatible_actions():
    txt = WORKFLOW.read_text(encoding="utf-8")
    assert "actions/checkout@v5" in txt
    assert "actions/setup-python@v6" in txt
