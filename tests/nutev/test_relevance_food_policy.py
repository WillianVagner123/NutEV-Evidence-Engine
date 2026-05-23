import json
from pathlib import Path

from nutev.analysis.relevance import score_record


def test_busca1_scoring_boosts_food_policy_and_labeling_documents():
    scoring_rules = json.loads(
        (Path(__file__).resolve().parents[2] / "config" / "scoring_rules.json").read_text(
            encoding="utf-8"
        )
    )
    base_record = {
        "source": "official",
        "url": "https://example.org/policy",
        "abstract": "Adult obesity prevention and healthy eating guidance in community settings.",
        "journal": "",
        "source_institution": "Ministry of Health",
    }

    generic_report = score_record(
        {
            **base_record,
            "title": "Healthy eating report for adult obesity prevention",
        },
        scoring_rules,
        "busca1",
    )
    policy_guidance = score_record(
        {
            **base_record,
            "title": "Food policy and front-of-pack labeling guidance for adult obesity prevention",
        },
        scoring_rules,
        "busca1",
    )

    assert policy_guidance["relevance_score"] > generic_report["relevance_score"]
