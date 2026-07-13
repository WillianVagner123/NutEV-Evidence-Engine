from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_obesity_watch_queries_cover_glp1_discontinuation_nutrition_terms() -> None:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "glp-1 discontinuation nutrition" in rendered
    assert "post-glp-1 weight maintenance nutrition" in rendered
    assert "nutrition care after glp-1 discontinuation" in rendered
    assert "dietitian-led care after anti-obesity medication discontinuation" in rendered


def test_glp1_discontinuation_nutrition_signal_scores_above_generic_pharmacotherapy() -> None:
    targeted = score_watch_item(
        {
            "title": "Nutrition care after GLP-1 discontinuation for obesity",
            "abstract": (
                "Dietitian-led care and dietary intervention after anti-obesity "
                "medication discontinuation for weight regain prevention."
            ),
            "source_provider": "pubmed",
        }
    )
    generic = score_watch_item(
        {
            "title": "GLP-1 receptor agonist discontinuation update",
            "abstract": "Medication persistence and safety report.",
            "source_provider": "pubmed",
        }
    )

    assert targeted > generic
