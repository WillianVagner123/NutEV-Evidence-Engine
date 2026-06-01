import importlib


def _score_watch_item(item):
    module = importlib.import_module("nutev.global_watch.watch_scoring")
    return module.score_watch_item(item)


def test_hybrid_implementation_trial_signal_improves_priority() -> None:
    assert _score_watch_item(
        {
            "title": "Hybrid effectiveness-implementation trial for dietary adherence in cardiometabolic care",
        }
    ) > _score_watch_item(
        {"title": "Dietary adherence in cardiometabolic care note"}
    )


def test_pragmatic_implementation_trial_signal_improves_priority() -> None:
    assert _score_watch_item(
        {
            "title": "Pragmatic implementation trial of nutrition care pathways for obesity",
        }
    ) > _score_watch_item({"title": "Nutrition care pathways for obesity note"})
