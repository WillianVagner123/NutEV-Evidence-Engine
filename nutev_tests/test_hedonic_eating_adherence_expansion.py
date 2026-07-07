from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def _config_root() -> Path:
    return Path(__file__).resolve().parents[1] / "config"


def test_hedonic_eating_supplement_is_loaded_for_intervention_and_framework_workstreams() -> None:
    taxonomy = load_json(_config_root() / "keyword_taxonomy.json")

    terms = taxonomy["global"]["implementation_behavior"]["hedonic_eating_adherence"]
    assert "food craving" in terms
    assert "hedonic hunger" in terms
    assert "Yale Food Addiction Scale" in terms

    busca2b = taxonomy["workstreams"]["busca2b"]
    assert "hedonic_eating_adherence" in busca2b["priority_outcomes"]
    assert "dietary lapse weight loss maintenance" in busca2b["web_query_hints"]

    framework = taxonomy["workstreams"]["artigo3_framework"]
    assert "hedonic_eating_adherence" in framework["priority_outcomes"]
    assert "Yale Food Addiction Scale validation" in framework["web_query_hints"]


def test_hedonic_eating_terms_render_in_provider_queries() -> None:
    taxonomy = load_json(_config_root() / "keyword_taxonomy.json")

    busca2b_queries = "\n".join(
        render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    ).lower()
    framework_queries = "\n".join(
        render_queries_for_provider(taxonomy, "artigo3_framework", "europepmc")
    ).lower()

    assert "food craving" in busca2b_queries
    assert "dietary lapse" in busca2b_queries
    assert "hedonic hunger" in framework_queries
    assert "yale food addiction scale" in framework_queries


def test_hedonic_eating_scoring_prioritizes_adherence_relevant_records() -> None:
    scoring_rules = load_json(_config_root() / "scoring_rules.json")
    base_record = {
        "title": "Lifestyle intervention for adults with obesity and cardiometabolic risk",
        "abstract": "Diet quality and physical activity support are described.",
        "journal": "Clinical Nutrition",
        "source": "pubmed",
        "url": "https://example.org/intervention",
    }
    targeted_record = {
        **base_record,
        "title": "Lifestyle intervention for food craving and dietary lapse in adults with obesity",
        "abstract": (
            "The behavioral nutrition intervention addresses hedonic hunger, "
            "emotional eating, relapse prevention and dietary adherence."
        ),
    }

    base_score = score_record(dict(base_record), scoring_rules, "busca2b")["relevance_score"]
    targeted_score = score_record(dict(targeted_record), scoring_rules, "busca2b")["relevance_score"]

    assert targeted_score > base_score
    assert targeted_score - base_score >= 9
