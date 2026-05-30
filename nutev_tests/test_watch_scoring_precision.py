from nutev.global_watch.watch_scoring import score_watch_item


def test_generic_framework_scale_terms_do_not_outscore_relevant_nutrition_note() -> None:
    generic = score_watch_item(
        {"title": "Framework for laboratory instrument scale development"}
    )
    relevant = score_watch_item({"title": "Obesity nutrition care note"})
    assert generic <= relevant


def test_questionnaire_validation_and_psychometric_signals_improve_priority() -> None:
    assert score_watch_item(
        {
            "title": "Food literacy questionnaire validation and psychometric study",
        }
    ) > score_watch_item({"title": "Food literacy note"})


def test_cardiometabolic_clinical_signals_improve_watch_priority() -> None:
    enriched = score_watch_item(
        {
            "title": (
                "Dietary adherence intervention for type 2 diabetes mellitus, "
                "glycemic control, HbA1c, and LDL cholesterol"
            ),
        }
    )
    generic = score_watch_item(
        {"title": "Dietary adherence intervention for diabetes and cholesterol"}
    )

    assert enriched > generic
