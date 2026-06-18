import importlib
import sys

from nutev.global_watch.watch_scoring import score_watch_item


def test_watch_scoring_import_still_avoids_pipeline_import() -> None:
    sys.modules.pop("nutev.global_watch.watch_pipeline", None)
    sys.modules.pop("nutev.global_watch.watch_scoring", None)

    importlib.import_module("nutev.global_watch.watch_scoring")

    assert "nutev.global_watch.watch_pipeline" not in sys.modules


def test_gestational_diabetes_guideline_is_deprioritized_vs_type_2_diabetes() -> None:
    gestational = score_watch_item(
        {
            "title": "gestational diabetes nutrition clinical practice guideline",
            "source_provider": "pubmed",
            "is_new": True,
        }
    )
    type_2 = score_watch_item(
        {
            "title": "type 2 diabetes nutrition clinical practice guideline",
            "source_provider": "pubmed",
            "is_new": True,
        }
    )

    assert gestational < type_2
