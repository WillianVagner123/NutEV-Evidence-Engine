from nutev.global_watch.watch_scoring import score_watch_item


def test_preclinical_animal_terms_are_downranked_against_human_relevant_notes() -> None:
    preclinical = score_watch_item(
        {
            "title": "Murine mouse model of ketogenic diet and cardiometabolic risk",
            "abstract": "Animal study in mice and rats.",
        }
    )
    human_relevant = score_watch_item(
        {"title": "Ketogenic diet for cardiometabolic risk note"}
    )

    assert preclinical < human_relevant


def test_rodent_language_offsets_diet_pattern_bonus() -> None:
    rodent_only = score_watch_item(
        {"title": "Rodent model of Mediterranean diet and obesity"}
    )
    human_relevant = score_watch_item(
        {"title": "Mediterranean diet for obesity note"}
    )

    assert rodent_only < human_relevant
