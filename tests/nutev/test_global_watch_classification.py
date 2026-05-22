from nutev.global_watch.watch_pipeline import (
    infer_evidence_type,
    infer_workstream_affinity,
)


def test_infer_evidence_type_recognizes_guideline_updates_and_network_reviews() -> None:
    assert (
        infer_evidence_type(
            "2026 Clinical Practice Update for MASLD nutrition care",
            "A network meta-analysis informed update for cardiometabolic risk care.",
            "https://example.org/update",
        )
        == "guideline"
    )

    assert (
        infer_evidence_type(
            "Network meta-analysis of Mediterranean diet interventions",
            "Living systematic review of adherence and glycemic outcomes.",
            "https://example.org/review",
        )
        == "systematic_review"
    )


def test_infer_workstream_affinity_routes_food_is_medicine_trials_to_busca2b() -> None:
    affinity = infer_workstream_affinity(
        "Medically tailored meals for type 2 diabetes and obesity",
        "implementation_behavior",
        abstract=(
            "Implementation outcomes, shared decision making and health coaching "
            "improved adherence in a randomized trial."
        ),
    )

    assert "busca2b" in affinity


def test_infer_workstream_affinity_routes_instruments_to_a3() -> None:
    affinity = infer_workstream_affinity(
        "Food literacy survey instrument for shared meals and cooking confidence",
        "frameworks_instruments",
        abstract="Questionnaire validation and scale development study.",
    )

    assert "a3" in affinity
