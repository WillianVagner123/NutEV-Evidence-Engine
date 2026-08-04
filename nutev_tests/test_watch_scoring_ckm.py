from nutev.global_watch.watch_scoring import score_watch_item


def test_ckm_nutrition_signal_is_kept_in_scope() -> None:
    item = {
        "title": "Cardiovascular-kidney-metabolic syndrome nutrition care pathway",
        "abstract": "CKM risk management with medical nutrition therapy and dietary pattern counseling.",
        "source_provider": "pubmed",
    }

    generic_item = {
        "title": "Nutrition care pathway note",
        "source_provider": "pubmed",
    }

    assert score_watch_item(item) > score_watch_item(generic_item)


def test_ckm_without_nutmev_anchor_does_not_get_scope_penalty() -> None:
    item = {
        "title": "CKM syndrome scientific statement",
        "abstract": "Cardio-kidney-metabolic health and cardiometabolic risk guidance.",
        "source_provider": "pubmed",
    }

    unrelated_item = {
        "title": "Scientific statement on unrelated specialty care",
        "source_provider": "pubmed",
    }

    assert score_watch_item(item) > score_watch_item(unrelated_item)
