from nutev.global_watch.watch_scoring import score_watch_item


def test_longitudinal_adherence_terms_improve_watch_priority() -> None:
    focused = score_watch_item(
        {
            "title": "Long-term weight loss maintenance and dietary self-monitoring for obesity care",
            "abstract": "Relapse prevention and weight regain prevention after lifestyle nutrition intervention.",
            "relevance_score": 1,
        }
    )
    generic = score_watch_item(
        {
            "title": "Lifestyle nutrition intervention for obesity care",
            "relevance_score": 1,
        }
    )

    assert focused > generic


def test_diet_quality_retention_terms_improve_watch_priority() -> None:
    focused = score_watch_item(
        {
            "title": "Diet quality, healthy eating index, engagement, and retention in cardiometabolic nutrition care",
            "relevance_score": 1,
        }
    )
    generic = score_watch_item(
        {
            "title": "Cardiometabolic nutrition care note",
            "relevance_score": 1,
        }
    )

    assert focused > generic
