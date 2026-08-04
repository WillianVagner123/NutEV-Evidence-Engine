from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.builders import build_queries
from nutev.settings import load_json


def test_steatotic_liver_supplement_reaches_busca2_queries() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    busca2a_queries = "\n".join(build_queries(taxonomy, "busca2a")).lower()
    busca2b_queries = "\n".join(build_queries(taxonomy, "busca2b")).lower()

    assert "sld practice guidance" in busca2a_queries
    assert "masld nutrition guideline" in busca2a_queries
    assert "nutrition therapy for masld" in busca2b_queries
    assert "mediterranean diet masld" in busca2b_queries


def test_steatotic_liver_supplement_boosts_guideline_and_diet_intervention_scores() -> None:
    scoring_rules = load_json(Path("config") / "scoring_rules.json")

    guideline_baseline = score_record(
        {
            "title": "Practice guidance for adult obesity with fatty liver disease",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )
    guideline_enriched = score_record(
        {
            "title": "SLD practice guidance and MASLD nutrition guideline for adult obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )
    intervention_baseline = score_record(
        {
            "title": "Lifestyle intervention for adult obesity with steatotic liver disease",
            "abstract": "Adults received general nutrition support with metabolic follow-up.",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    intervention_enriched = score_record(
        {
            "title": "Nutrition therapy for MASLD with Mediterranean diet MASLD lifestyle intervention",
            "abstract": "Adults with obesity had liver fat reduction and steatosis improvement.",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert guideline_enriched["relevance_score"] > guideline_baseline["relevance_score"]
    assert intervention_enriched["relevance_score"] > intervention_baseline["relevance_score"]
