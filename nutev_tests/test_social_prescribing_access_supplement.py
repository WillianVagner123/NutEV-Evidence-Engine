from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def test_social_prescribing_access_terms_load_into_busca2b_querypack() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    joined = "\n".join(queries).lower()

    assert "social prescribing nutrition" in joined
    assert "closed-loop referral" in joined or "closed loop referral" in joined
    assert "community health worker nutrition" in joined
    assert "nutrition security referral" in joined


def test_social_prescribing_access_terms_receive_relevance_boost() -> None:
    scoring = load_json(Path("config") / "scoring_rules.json")
    base_record = {
        "source": "pubmed",
        "url": "https://example.org/social-prescribing-nutrition",
        "abstract": "Adult obesity and cardiometabolic risk nutrition care in primary care.",
        "journal": "",
        "source_institution": "",
    }

    generic = score_record(
        {
            **base_record,
            "title": "Nutrition referral intervention for adults with obesity",
        },
        scoring,
        "busca2b",
    )
    social_prescribing = score_record(
        {
            **base_record,
            "title": "Social prescribing nutrition with closed-loop referral and community health worker nutrition support for adults with obesity",
        },
        scoring,
        "busca2b",
    )

    assert social_prescribing["relevance_score"] > generic["relevance_score"]


def test_busca1_social_prescribing_access_hints_are_auditable() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")
    busca1 = taxonomy["workstreams"]["busca1"]

    assert "social prescribing nutrition report" in busca1["web_query_hints"]
    assert "closed-loop referral food insecurity report" in busca1["web_query_hints"]
    assert "nutrition security referral" in taxonomy["global"]["implementation_behavior"]["social_prescribing_access"]
