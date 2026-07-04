from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_obesity_queries_add_vascular_and_metabolic_context_terms() -> None:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "metabolic syndrome" in rendered
    assert "type 2 diabetes" in rendered
    assert "hypertension" in rendered
    assert "cardiovascular disease" in rendered
    assert "coronary artery disease" in rendered
    assert "atherosclerotic cardiovascular disease" in rendered
    assert '"ascvd"' in rendered
    assert '"masld"' in rendered
    assert '"nafld"' in rendered
    assert '"mash"' in rendered


def test_obesity_queries_include_ckm_cardiometabolic_terms() -> None:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "cardiovascular-kidney-metabolic syndrome" in rendered
    assert "cardiovascular kidney metabolic risk" in rendered
    assert '"ckm syndrome"' in rendered
    assert '"ckm risk"' in rendered


def test_cardiometabolic_vascular_signals_improve_priority() -> None:
    enriched = score_watch_item(
        {
            "title": (
                "Atherosclerotic cardiovascular disease and coronary artery disease "
                "risk reduction with nutrition therapy in metabolic syndrome"
            ),
            "abstract": "ASCVD prevention in obesity and type 2 diabetes.",
        }
    )
    generic = score_watch_item({"title": "Nutrition therapy note"})

    assert enriched > generic


def test_ckm_signals_improve_priority() -> None:
    enriched = score_watch_item(
        {
            "title": "Cardiovascular-kidney-metabolic syndrome and nutrition therapy",
            "abstract": "CKM risk management in adults with obesity and type 2 diabetes.",
        }
    )
    generic = score_watch_item({"title": "Nutrition therapy note"})

    assert enriched > generic
