from __future__ import annotations

from nutev.global_watch.watch_pipeline import infer_workstream_affinity


def test_diabetes_remission_maps_to_clinical_and_intervention_workstreams() -> None:
    affinity = infer_workstream_affinity(
        "Nutrition care for type 2 diabetes remission and weight regain prevention",
        "obesity_cardiometabolic",
    )

    assert "busca2a" in affinity
    assert "busca2b" in affinity


def test_personalized_nutrition_maps_to_intervention_workstream() -> None:
    affinity = infer_workstream_affinity(
        "Personalized dietary intervention and individualized meal plan for obesity care",
        "implementation_behavior",
    )

    assert "busca2b" in affinity
