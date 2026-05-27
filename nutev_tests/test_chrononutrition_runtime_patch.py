from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item
from nutev.querypacks.builders import build_queries
from nutev.settings import load_json


def test_busca2b_runtime_queries_include_chrononutrition_terms() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")
    queries = [query.lower() for query in build_queries(taxonomy, "busca2b")]

    assert any(
        "chrononutrition" in query
        or "meal timing" in query
        or "time-restricted feeding" in query
        or "early time-restricted eating" in query
        for query in queries
    )
    assert any(
        ("chrononutrition" in query or "meal timing" in query)
        and (
            "randomized controlled trial" in query
            or "systematic review" in query
            or "implementation" in query
        )
        for query in queries
    )


def test_diet_pattern_watch_queries_include_chrononutrition_terms_in_quick_mode() -> None:
    rows = build_watch_queries(["diet_patterns"], 7, "quick")
    rendered = " ".join(str(row["query"]) for row in rows).lower()

    assert "chrononutrition" in rendered
    assert "meal timing" in rendered
    assert "time-restricted feeding" in rendered or "early time-restricted eating" in rendered


def test_chrononutrition_terms_raise_watch_and_relevance_scores() -> None:
    generic_item = {
        "title": "General nutrition support in adults",
        "abstract": "A broad nutrition note without a timing intervention.",
        "category": "diet_patterns",
        "source_provider": "pubmed",
        "source": "pubmed",
    }
    chrono_item = {
        "title": "Early time-restricted eating chrononutrition trial in adults with obesity and prediabetes",
        "abstract": "Meal timing intervention improved adherence and glycemic control.",
        "category": "diet_patterns",
        "source_provider": "pubmed",
        "source": "pubmed",
    }

    assert score_watch_item(chrono_item) > score_watch_item(generic_item)

    generic_record = score_record(
        {
            "title": "General nutrition counseling in adults",
            "abstract": "A broad lifestyle note.",
            "source": "pubmed",
        },
        {},
        "busca2b",
    )
    chrono_record = score_record(
        {
            "title": "Chrononutrition and meal timing trial for adults with obesity and prediabetes",
            "abstract": "Early time-restricted eating improved adherence and glycemic control.",
            "source": "pubmed",
        },
        {},
        "busca2b",
    )

    assert chrono_record["relevance_score"] > generic_record["relevance_score"]
