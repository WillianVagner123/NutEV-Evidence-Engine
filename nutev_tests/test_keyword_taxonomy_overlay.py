from pathlib import Path

from nutev.querypacks.builders import build_structured_components
from nutev.settings import load_json


def test_keyword_taxonomy_overlay_extends_busca2b_masld_and_adherence_terms():
    repo_root = Path(__file__).resolve().parents[1]
    taxonomy = load_json(repo_root / "config" / "keyword_taxonomy.json")

    _, components = build_structured_components(taxonomy, "busca2b")

    assert "fatty_liver" in taxonomy["workstreams"]["busca2b"]["clinical_keys"]
    assert "metabolic dysfunction-associated steatotic liver disease" in components["clinical_terms"]
    assert "dietary adherence" in components["behavior_terms"]
    assert "long-term adherence" in components["priority_outcomes"]
