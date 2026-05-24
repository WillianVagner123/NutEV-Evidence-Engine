import json
from pathlib import Path

from nutev.analysis.relevance import score_record


def test_scoring_boosts_abstract_only_food_as_medicine_variants() -> None:
    scoring_rules = json.loads(
        (Path(__file__).resolve().parents[2] / "config" / "scoring_rules.json").read_text(
            encoding="utf-8"
        )
    )
    base_record = {
        "source": "pubmed",
        "url": "https://example.org/nutmev-food-as-medicine",
        "journal": "",
        "source_institution": "",
    }

    control = score_record(
        {
            **base_record,
            "title": "Nutrition support program for adult obesity",
            "abstract": "Adult obesity support delivered in primary care.",
        },
        scoring_rules,
        "busca2b",
    )
    boosted = score_record(
        {
            **base_record,
            "title": "Nutrition support program for adult obesity",
            "abstract": (
                "Adult obesity support delivered in primary care with food as medicine "
                "intervention pathways, produce rx access, healthy food prescription, "
                "and teaching kitchens."
            ),
        },
        scoring_rules,
        "busca2b",
    )

    assert boosted["relevance_score"] > control["relevance_score"]
