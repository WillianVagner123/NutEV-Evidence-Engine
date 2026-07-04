from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.builders import build_querypack
from nutev.settings import load_json


def test_group_care_supplement_reaches_busca2b_querypack() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    qpack = build_querypack(taxonomy, ["busca2b"])
    rendered = "\n".join(qpack["busca2b"]).lower()

    assert "shared medical appointment for diabetes" in rendered
    assert "group visit for medical nutrition therapy" in rendered
    assert "group nutrition visit" in rendered


def test_group_care_scoring_supplement_prioritizes_busca2b_records() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Shared medical appointment for diabetes with medical nutrition therapy and weight management",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Diabetes medical nutrition therapy and weight management",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
