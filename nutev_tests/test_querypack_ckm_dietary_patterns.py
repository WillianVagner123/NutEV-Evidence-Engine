from pathlib import Path

from nutev.querypacks.builders import build_structured_components
from nutev.settings import load_json


def test_busca2a_and_busca2b_include_ckm_and_therapeutic_diet_terms() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    _, busca2a = build_structured_components(taxonomy, "busca2a")
    _, busca2b = build_structured_components(taxonomy, "busca2b")

    busca2a_conditions = {term.lower() for term in busca2a["condition_terms"]}
    busca2a_hints = {term.lower() for term in busca2a["web_hints"]}
    busca2b_conditions = {term.lower() for term in busca2b["condition_terms"]}
    busca2b_hints = {term.lower() for term in busca2b["web_hints"]}
    diet_terms = {term.lower() for term in busca2b["diet_terms"]}

    assert "cardiovascular-kidney-metabolic syndrome" in busca2a_conditions
    assert "ckm syndrome" in busca2a_conditions
    assert "cardiometabolic multimorbidity" in busca2b_conditions
    assert "ckm syndrome lifestyle intervention" in busca2b_hints
    assert "ckm health scientific statement" in busca2a_hints
    assert "therapeutic dietary pattern" in diet_terms
    assert "dietary pattern prescription" in diet_terms
    assert "portfolio diet prescription" in diet_terms
