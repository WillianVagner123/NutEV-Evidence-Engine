import importlib
import sys


def _score_watch_item(item):
    module = importlib.import_module("nutev.global_watch.watch_scoring")
    return module.score_watch_item(item)


def test_scoring_import_does_not_load_watch_pipeline():
    # Keep this test independent from pytest collection/order. Other tests may
    # legitimately import the full watch pipeline before this module runs; the
    # contract we want to assert here is narrower: importing watch_scoring alone
    # must not import watch_pipeline.
    sys.modules.pop("nutev.global_watch.watch_pipeline", None)
    sys.modules.pop("nutev.global_watch.watch_scoring", None)

    importlib.import_module("nutev.global_watch.watch_scoring")

    assert "nutev.global_watch.watch_pipeline" not in sys.modules


def test_guideline_scores_more_than_editorial():
    assert _score_watch_item({"title": "new guideline", "source_provider": "pubmed"}) > _score_watch_item({"title": "editorial note", "source_provider": "pubmed"})


def test_systematic_review_scores_more_than_generic():
    assert _score_watch_item({"title": "systematic review of diet"}) > _score_watch_item({"title": "diet study"})


def test_pdf_scores_more_than_metadata_only():
    assert _score_watch_item({"title": "trial", "download_status": "pdf"}) > _score_watch_item({"title": "trial", "download_status": "metadata_only"})


def test_official_sources_bonus():
    assert _score_watch_item({"title": "report", "source_provider": "official_sources"}) > _score_watch_item({"title": "report", "source_provider": "crossref"})


def test_lifestyle_intervention_alias_scores_above_generic_lifestyle() -> None:
    assert _score_watch_item({"title": "therapeutic lifestyle changes for diabetes"}) > _score_watch_item({"title": "lifestyle counseling for diabetes"})


def test_masld_alias_scores_above_generic_liver_study() -> None:
    assert _score_watch_item({"title": "metabolic dysfunction-associated steatotic liver disease guideline"}) > _score_watch_item({"title": "liver disease guideline"})


def test_food_environment_and_commensality_boost_scope_relevance() -> None:
    assert _score_watch_item({"title": "food environment and commensality intervention"}) > _score_watch_item({"title": "community nutrition intervention"})