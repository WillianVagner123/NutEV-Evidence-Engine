from nutev.querypacks.semantic_blocks import semantic_terms
from nutev.settings import default_config_root, load_json


def test_busca2a_semantic_terms_include_ckm_variants() -> None:
    terms = {term.lower() for term in semantic_terms("busca2a", min_priority=5)}

    assert "cardiovascular-kidney-metabolic syndrome" in terms
    assert "cardiovascular kidney metabolic syndrome" in terms
    assert "ckm syndrome" in terms


def test_busca2b_semantic_document_terms_include_ckm_evidence_types() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", field="document_terms", min_priority=5)}

    assert "presidential advisory" in terms
    assert "clinical decision pathway" in terms


def test_cardiorenal_supplements_include_ckm_nutrition_signals() -> None:
    config_root = default_config_root()
    taxonomy = load_json(config_root / "keyword_taxonomy.json")
    scoring = load_json(config_root / "scoring_rules.json")

    busca2b_terms = {
        term.lower()
        for term in taxonomy["workstreams"]["busca2b"]["condition_terms"]
    }
    busca2b_hints = {
        term.lower()
        for term in taxonomy["workstreams"]["busca2b"]["web_query_hints"]
    }

    assert "cardiovascular-kidney-metabolic nutrition" in busca2b_terms
    assert "ckm dietary intervention" in busca2b_terms
    assert "ckm lifestyle medicine" in busca2b_terms
    assert "ckm nutrition systematic review" in busca2b_hints
    assert scoring["keyword_points"]["ckm nutrition"] == 4
    assert scoring["workstream_bonus"]["busca2b"]["ckm dietary intervention"] == 6
