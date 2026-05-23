from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_lifestyle_watch_queries_cover_food_is_medicine_program_variants() -> None:
    queries = build_watch_queries(["lifestyle_medicine"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "produce prescription program" in rendered
    assert "produce rx" in rendered
    assert "fruit and vegetable prescription" in rendered
    assert "food prescription program" in rendered


def test_implementation_watch_queries_cover_food_is_medicine_program_variants() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "produce prescription program" in rendered
    assert "healthy food prescription" in rendered
    assert "food prescription program" in rendered


def test_food_is_medicine_program_terms_score_above_generic_note() -> None:
    plain_score = score_watch_item(
        {"title": "Lifestyle medicine nutrition update", "source_provider": "pubmed"}
    )
    enriched_score = score_watch_item(
        {
            "title": "Produce Rx and food prescription program for cardiometabolic nutrition care",
            "abstract": "Fruit and vegetable prescription delivery was evaluated in a food is medicine program.",
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )

    assert enriched_score > plain_score + 35
