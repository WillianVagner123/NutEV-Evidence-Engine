from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "apps" / "nutev-validation"


def test_launcher_does_not_probe_round_before_scientific_readiness() -> None:
    js = (VALIDATION / "launcher.js").read_text(encoding="utf-8")

    assert "const readiness = await loadReadiness()" in js
    assert "const round = readiness.ready === true ? await loadRound() : null" in js
    assert "Promise.all([loadReadiness(), loadRound()])" not in js


def test_decision_layer_gates_round_fetch_on_readiness() -> None:
    js = (VALIDATION / "decision-ui.js").read_text(encoding="utf-8")

    assert "async function validationReadyForRound()" in js
    assert "fetch('/api/validation/readiness'" in js
    assert "return readiness.ready === true" in js
    assert "if (!(await validationReadyForRound())) return" in js
    assert js.index("if (!(await validationReadyForRound())) return") < js.index("fetch('/api/validation/round'")
