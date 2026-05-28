from __future__ import annotations

from pathlib import Path

from nutev.querypacks.builders import build_structured_components
from nutev.settings import load_json


ADVANCED_LIPID_TERMS = {
    "non-hdl cholesterol",
    "non hdl cholesterol",
    "apolipoprotein b",
    "apob",
    "remnant cholesterol",
    "triglyceride-rich lipoprotein",
    "triglyceride rich lipoprotein",
    "hypertriglyceridemia",
    "hypertriglyceridaemia",
}


def _priority_outcomes_for(workstream: str) -> set[str]:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    _, components = build_structured_components(taxonomy, workstream)
    return {term.lower() for term in components["priority_outcomes"]}


def test_busca2a_priority_outcomes_include_advanced_lipid_markers() -> None:
    outcomes = _priority_outcomes_for("busca2a")

    assert ADVANCED_LIPID_TERMS.issubset(outcomes)


def test_busca2b_priority_outcomes_include_advanced_lipid_markers() -> None:
    outcomes = _priority_outcomes_for("busca2b")

    assert ADVANCED_LIPID_TERMS.issubset(outcomes)
