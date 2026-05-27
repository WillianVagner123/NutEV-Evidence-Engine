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


def test_guidance_advisory_variants_score_more_than_generic_note():
    assert _score_watch_item(
        {
            "title": "Scientific advisory and best practice advice for obesity nutrition care",
        }
    ) > _score_watch_item({"title": "obesity nutrition care note"})


def test_consensus_guidance_scores_more_than_generic_note():
    assert _score_watch_item(
        {"title": "Consensus guidance for cardiometabolic nutrition care"}
    ) > _score_watch_item({"title": "cardiometabolic nutrition care note"})


def test_process_evaluation_and_barriers_bonus_improves_priority():
    assert _score_watch_item({"title": "process evaluation of barriers and facilitators for dietary adherence"}) > _score_watch_item({"title": "dietary adherence note"})


def test_taxonomy_aligned_behavioral_signals_improve_priority():
    assert _score_watch_item({"title": "behavioral lifestyle intervention with goal setting and social support"}) > _score_watch_item({"title": "lifestyle intervention note"})


def test_taxonomy_aligned_food_literacy_signals_improve_priority():
    assert _score_watch_item({"title": "nutrition literacy, family meals, and food access in obesity care"}) > _score_watch_item({"title": "obesity care note"})


def test_whole_food_plant_based_signal_improves_priority():
    assert _score_watch_item({"title": "whole-food plant-based diet for cardiometabolic risk"}) > _score_watch_item({"title": "diet for cardiometabolic risk"})


def test_ultra_processed_and_nova_signals_improve_priority():
    assert _score_watch_item(
        {"title": "Ultra-processed food exposure using NOVA classification in obesity care"}
    ) > _score_watch_item({"title": "Obesity care note"})


def test_implementation_fidelity_and_sustainability_improve_priority():
    assert _score_watch_item({"title": "implementation fidelity and sustainability for lifestyle nutrition programs"}) > _score_watch_item({"title": "lifestyle nutrition programs note"})


def test_medical_nutrition_therapy_and_counselling_improve_priority():
    assert _score_watch_item({"title": "medical nutrition therapy and nutrition counselling for obesity"}) > _score_watch_item({"title": "obesity note"})


def test_dietary_counselling_variants_improve_priority() -> None:
    assert _score_watch_item(
        {"title": "dietary counseling and dietary counselling for obesity care"}
    ) > _score_watch_item({"title": "obesity care note"})


def test_standards_of_care_scores_more_than_generic_report():
    assert _score_watch_item({"title": "Standards of Care in Diabetes nutrition update"}) > _score_watch_item({"title": "Diabetes nutrition report"})


def test_clinical_pathway_scores_more_than_generic_note():
    assert _score_watch_item({"title": "Clinical pathway for obesity and cardiometabolic nutrition care"}) > _score_watch_item({"title": "Obesity and cardiometabolic nutrition care note"})


def test_clinical_decision_pathway_scores_more_than_generic_note():
    assert _score_watch_item({"title": "Clinical decision pathway for obesity and cardiometabolic nutrition care"}) > _score_watch_item({"title": "Obesity and cardiometabolic nutrition care note"})


def test_joint_guideline_scores_more_than_generic_note():
    assert _score_watch_item({"title": "Joint guideline for obesity and cardiometabolic nutrition care"}) > _score_watch_item({"title": "Obesity and cardiometabolic nutrition care note"})


def test_living_guideline_scores_more_than_generic_note():
    assert _score_watch_item({"title": "Living guideline for obesity and cardiometabolic nutrition care"}) > _score_watch_item({"title": "Obesity and cardiometabolic nutrition care note"})


def test_long_form_dash_signal_scores_more_than_generic_hypertension_note():
    assert _score_watch_item(
        {"title": "Dietary Approaches to Stop Hypertension for cardiometabolic risk"}
    ) > _score_watch_item({"title": "Hypertension note"})


def test_new_nordic_and_plant_based_variants_improve_priority():
    assert _score_watch_item(
        {"title": "New Nordic diet and plant based diet for obesity care"}
    ) > _score_watch_item({"title": "Diet for obesity care"})


def test_therapeutic_lifestyle_changes_and_healthy_eating_pattern_improve_priority():
    assert _score_watch_item(
        {"title": "Therapeutic lifestyle changes and healthy eating pattern for cardiometabolic risk"}
    ) > _score_watch_item({"title": "Cardiometabolic risk note"})


def test_lifestyle_intervention_variants_improve_priority():
    assert _score_watch_item(
        {
            "title": "Intensive lifestyle intervention, intermittent fasting, and diabetes prevention program for obesity care",
        }
    ) > _score_watch_item({"title": "Obesity care note"})


def test_living_systematic_review_and_rapid_review_improve_priority():
    assert _score_watch_item(
        {"title": "Living systematic review and rapid review of Mediterranean diet for obesity"}
    ) > _score_watch_item({"title": "Mediterranean diet for obesity note"})


def test_abstract_only_guideline_signal_improves_priority():
    assert _score_watch_item(
        {
            "title": "Nutrition update",
            "abstract": "Clinical practice guideline for obesity and cardiometabolic risk",
        }
    ) > _score_watch_item({"title": "Nutrition update"})


def test_snippet_only_editorial_signal_reduces_priority():
    assert _score_watch_item(
        {
            "title": "Lifestyle medicine update",
            "snippet": "Editorial commentary on lifestyle medicine",
        }
    ) < _score_watch_item({"title": "Lifestyle medicine update"})


def test_mash_and_nonalcoholic_fatty_liver_disease_signals_improve_priority():
    assert _score_watch_item(
        {
            "title": "Medical nutrition therapy for MASH and nonalcoholic fatty liver disease",
        }
    ) > _score_watch_item({"title": "Medical nutrition therapy note"})


def test_culinary_training_and_food_literacy_signals_improve_priority():
    assert _score_watch_item(
        {
            "title": "Teaching kitchens, culinary nutrition, and cooking confidence for food literacy",
        }
    ) > _score_watch_item({"title": "Food literacy note"})


def test_home_cooking_and_meal_preparation_signals_improve_priority():
    assert _score_watch_item(
        {
            "title": "Home cooking, meal preparation, and nutrition education in obesity care",
        }
    ) > _score_watch_item({"title": "Obesity care note"})


def test_cfir_long_form_signal_improves_priority() -> None:
    assert _score_watch_item(
        {"title": "Consolidated framework for implementation research in dietary adherence"}
    ) > _score_watch_item({"title": "Dietary adherence note"})


def test_audit_and_feedback_signal_improves_priority() -> None:
    assert _score_watch_item(
        {"title": "Audit and feedback for lifestyle nutrition care delivery"}
    ) > _score_watch_item({"title": "Lifestyle nutrition note"})


def test_health_coaching_and_practice_facilitation_improve_priority() -> None:
    assert _score_watch_item(
        {"title": "Health coaching and practice facilitation for lifestyle nutrition implementation"}
    ) > _score_watch_item({"title": "Lifestyle nutrition implementation note"})


def test_food_as_medicine_voucher_and_pantry_variants_improve_priority() -> None:
    assert _score_watch_item(
        {
            "title": "Healthy food incentives, produce vouchers, and medically tailored pantry support for cardiometabolic care",
        }
    ) > _score_watch_item({"title": "Cardiometabolic care note"})
