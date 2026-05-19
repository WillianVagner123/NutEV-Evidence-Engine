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


def test_implementation_science_bonus_improves_priority():
    assert _score_watch_item({"title": "implementation science for dietary adherence in lifestyle medicine"}) > _score_watch_item({"title": "lifestyle medicine note"})


def test_food_environment_bonus_improves_priority():
    assert _score_watch_item({"title": "food environment and shared meals in obesity prevention"}) > _score_watch_item({"title": "obesity prevention note"})


def test_practice_advisory_scores_more_than_generic_note():
    assert _score_watch_item({"title": "practice advisory for obesity nutrition care"}) > _score_watch_item({"title": "obesity nutrition care note"})


def test_process_evaluation_and_barriers_bonus_improves_priority():
    assert _score_watch_item({"title": "process evaluation of barriers and facilitators for dietary adherence"}) > _score_watch_item({"title": "dietary adherence note"})


def test_taxonomy_aligned_behavioral_signals_improve_priority():
    assert _score_watch_item({"title": "behavioral lifestyle intervention with goal setting and social support"}) > _score_watch_item({"title": "lifestyle intervention note"})


def test_taxonomy_aligned_food_literacy_signals_improve_priority():
    assert _score_watch_item({"title": "nutrition literacy, family meals, and food access in obesity care"}) > _score_watch_item({"title": "obesity care note"})


def test_whole_food_plant_based_signal_improves_priority():
    assert _score_watch_item({"title": "whole-food plant-based diet for cardiometabolic risk"}) > _score_watch_item({"title": "diet for cardiometabolic risk"})


def test_implementation_fidelity_and_sustainability_improve_priority():
    assert _score_watch_item({"title": "implementation fidelity and sustainability for lifestyle nutrition programs"}) > _score_watch_item({"title": "lifestyle nutrition programs note"})


def test_medical_nutrition_therapy_and_counselling_improve_priority():
    assert _score_watch_item({"title": "medical nutrition therapy and nutrition counselling for obesity"}) > _score_watch_item({"title": "obesity note"})
