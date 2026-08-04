from nutev.global_watch.cardiometabolic_remission_terms import (
    cardiometabolic_remission_terms,
)


def test_cardiometabolic_remission_terms_cover_diabetes_and_maintenance_axes():
    terms = cardiometabolic_remission_terms()
    lowered = {term.lower() for term in terms}

    assert "type 2 diabetes remission" in lowered
    assert "remission of type 2 diabetes" in lowered
    assert "lifestyle-induced diabetes remission" in lowered
    assert "weight regain prevention" in lowered
    assert "long-term weight loss maintenance" in lowered
    assert "dietary self-monitoring" in lowered


def test_cardiometabolic_remission_terms_deduplicate_case_insensitively():
    terms = cardiometabolic_remission_terms(
        [
            "Type 2 Diabetes Remission",
            "nutrition care for diabetes remission",
            "nutrition care for diabetes remission",
        ]
    )

    assert len(terms) == len({term.lower() for term in terms})
    assert terms[-1] == "nutrition care for diabetes remission"
