from __future__ import annotations

from pathlib import Path

from nutev.querypacks.builders import build_queries, build_structured_components
from nutev.settings import load_json


ROOT = Path(__file__).resolve().parents[1]


def test_cardiometabolic_obesity_supplement_reaches_clinical_workstreams() -> None:
    taxonomy = load_json(ROOT / "config" / "keyword_taxonomy.json")

    _, busca2a = build_structured_components(taxonomy, "busca2a")
    _, busca2b = build_structured_components(taxonomy, "busca2b")

    assert "complications-centric obesity" in busca2a["condition_terms"]
    assert "cardiometabolic-based chronic disease" in busca2a["condition_terms"]
    assert "cardiometabolic obesity nutrition intervention" in busca2b["focus_terms"]

    busca2a_queries = build_queries(taxonomy, "busca2a")
    busca2b_queries = build_queries(taxonomy, "busca2b")

    assert any("complications-centric obesity" in query for query in busca2a_queries)
    assert any("cardiometabolic obesity nutrition intervention" in query for query in busca2b_queries)
