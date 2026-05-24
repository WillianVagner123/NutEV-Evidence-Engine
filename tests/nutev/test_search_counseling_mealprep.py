import json
from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.builders import build_structured_components
from nutev.querypacks.provider_queries import render_queries_for_provider


def _load_taxonomy() -> dict:
    return json.loads(
        (Path(__file__).resolve().parents[2] / "config" / "keyword_taxonomy.json").read_text(
            encoding="utf-8"
        )
    )


def _load_scoring_rules() -> dict:
    return json.loads(
        (Path(__file__).resolve().parents[2] / "config" / "scoring_rules.json").read_text(
            encoding="utf-8"
        )
    )


def test_real_taxonomy_exposes_counseling_and_meal_preparation_terms():
    taxonomy = _load_taxonomy()

    _, components = build_structured_components(taxonomy, "busca2b")
    nutrition_terms = set(components["nutrition_terms"])
    web_hints = set(components["web_hints"])

    assert "dietary counseling" in nutrition_terms
    assert "dietary counselling" in nutrition_terms
    assert "meal preparation" in nutrition_terms
    assert "dietary counseling" in web_hints
    assert "meal preparation" in web_hints


def test_provider_queries_keep_counseling_and_meal_preparation_visible():
    taxonomy = _load_taxonomy()

    queries = render_queries_for_provider(taxonomy, "artigo3_framework", "pubmed")

    assert any(
        "dietary counseling" in query or "dietary counselling" in query
        for query in queries
    )
    assert any("meal preparation" in query for query in queries)


def test_scoring_rewards_counseling_meal_prep_and_family_meals_signals():
    scoring_rules = _load_scoring_rules()
    base_record = {
        "source": "pubmed",
        "url": "https://example.org/framework",
        "abstract": "Adult food literacy and culinary medicine support in lifestyle medicine.",
        "journal": "",
        "source_institution": "",
    }

    generic_framework = score_record(
        {
            **base_record,
            "title": "Framework for adult food literacy in lifestyle medicine",
        },
        scoring_rules,
        "artigo3_framework",
    )
    counseling_framework = score_record(
        {
            **base_record,
            "title": "Family meals, dietary counseling and meal preparation framework for adult food literacy in lifestyle medicine",
        },
        scoring_rules,
        "artigo3_framework",
    )

    assert counseling_framework["relevance_score"] > generic_framework["relevance_score"]
