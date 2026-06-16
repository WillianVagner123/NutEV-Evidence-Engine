from pathlib import Path


def test_sitecustomize_expands_cardiometabolic_diet_terms() -> None:
    text = Path("src/sitecustomize.py").read_text(encoding="utf-8")

    expected_terms = [
        "DASH eating plan",
        "TLC diet",
        "therapeutic lifestyle changes diet",
        "heart-healthy diet",
        "cardioprotective diet",
        "diet quality",
        "healthy eating pattern",
    ]
    for term in expected_terms:
        assert term in text

    assert "type 2 diabetes" in text
    assert "dyslipidemia" in text
