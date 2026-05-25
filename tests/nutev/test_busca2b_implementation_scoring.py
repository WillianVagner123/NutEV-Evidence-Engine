import json
from pathlib import Path

from nutev.analysis.relevance import score_record


def test_busca2b_scoring_boosts_implementation_outcome_signals():
    scoring_rules = json.loads(
        (Path(__file__).resolve().parents[2] / "config" / "scoring_rules.json").read_text(
            encoding="utf-8"
        )
    )

    base_record = {
        "source": "pubmed",
        "url": "https://example.org/implementation-study",
        "abstract": "Adult obesity and type 2 diabetes nutrition care in primary care.",
        "journal": "",
        "source_institution": "",
    }

    standard_record = score_record(
        {
            **base_record,
            "title": "Implementation study of nutrition care for adult obesity and type 2 diabetes",
        },
        scoring_rules,
        "busca2b",
    )
    implementation_outcomes_record = score_record(
        {
            **base_record,
            "title": "Implementation study of nutrition care for adult obesity and type 2 diabetes with adoption, reach, maintenance, sustainability and implementation cost outcomes",
        },
        scoring_rules,
        "busca2b",
    )

    assert (
        implementation_outcomes_record["relevance_score"]
        > standard_record["relevance_score"]
    )
