from __future__ import annotations

import json
from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms


def _load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_busca2b_semantic_terms_interleave_high_priority_blocks() -> None:
    terms = semantic_terms("busca2b", min_priority=4)

    assert terms[:5] == [
        "adherence",
        "implementation science",
        "food literacy",
        "dietary adherence",
        "process evaluation",
    ]


def test_provider_queries_expose_new_implementation_and_environment_terms() -> None:
    taxonomy = _load_json("config/keyword_taxonomy.json")

    busca2b_queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    artigo3_queries = render_queries_for_provider(taxonomy, "a3", "europepmc")

    assert any("process evaluation" in query.lower() for query in busca2b_queries)
    assert any("implementation science" in query.lower() for query in busca2b_queries)
    assert any("food environment" in query.lower() for query in artigo3_queries)


def test_scoring_rules_boost_implementation_and_food_environment_records() -> None:
    scoring_rules = _load_json("config/scoring_rules.json")

    baseline = score_record(
        {
            "title": "Mediterranean diet intervention in adults with obesity",
            "abstract": "Lifestyle modification study in adults.",
            "url": "https://example.org/base",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    enriched = score_record(
        {
            "title": "Process evaluation of an implementation strategy to improve food environment and shopping skills in adults with obesity",
            "abstract": "Knowledge translation and practice facilitation were used to support adherence.",
            "url": "https://example.org/enriched",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert enriched["relevance_score"] > baseline["relevance_score"]
