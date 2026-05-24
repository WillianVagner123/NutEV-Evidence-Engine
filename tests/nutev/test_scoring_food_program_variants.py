import json
from pathlib import Path

from nutev.analysis.relevance import score_record


def test_busca2b_scoring_rewards_food_program_variants() -> None:
    scoring_rules = json.loads(
        (Path(__file__).resolve().parents[2] / "config" / "scoring_rules.json").read_text(
            encoding="utf-8"
        )
    )
    base_record = {
        "source": "pubmed",
        "url": "https://example.org/program",
        "abstract": "Adult obesity and cardiometabolic nutrition support in primary care.",
        "journal": "",
        "source_institution": "",
    }

    generic_program = score_record(
        {
            **base_record,
            "title": "Community nutrition program for adult obesity",
        },
        scoring_rules,
        "busca2b",
    )
    enriched_program = score_record(
        {
            **base_record,
            "title": "Produce Rx and healthy food prescription program for adult obesity",
            "abstract": "Fruit and vegetable prescription delivery was evaluated in a food as medicine intervention.",
        },
        scoring_rules,
        "busca2b",
    )

    assert enriched_program["relevance_score"] > generic_program["relevance_score"] + 20


def test_busca2b_scoring_aligns_food_as_medicine_program_labels() -> None:
    scoring_rules = json.loads(
        (Path(__file__).resolve().parents[2] / "config" / "scoring_rules.json").read_text(
            encoding="utf-8"
        )
    )
    base_record = {
        "source": "pubmed",
        "url": "https://example.org/program-variant",
        "abstract": "Program implementation for adult obesity and cardiometabolic care.",
        "journal": "",
        "source_institution": "",
    }

    food_is_medicine = score_record(
        {
            **base_record,
            "title": "Food is medicine program for adult obesity",
        },
        scoring_rules,
        "busca2b",
    )
    food_as_medicine = score_record(
        {
            **base_record,
            "title": "Food as medicine program for adult obesity",
        },
        scoring_rules,
        "busca2b",
    )

    assert food_as_medicine["relevance_score"] >= food_is_medicine["relevance_score"]
