import importlib


def _score_watch_item(item):
    module = importlib.import_module("nutev.global_watch.watch_scoring")
    return module.score_watch_item(item)


def test_generic_implementation_signal_is_downranked_without_nutev_anchor() -> None:
    assert _score_watch_item(
        {"title": "Sustainability and service delivery in hospital operations"}
    ) < _score_watch_item({"title": "Hospital operations report"})


def test_nutev_anchored_implementation_signal_keeps_priority() -> None:
    assert _score_watch_item(
        {"title": "Sustainability for lifestyle nutrition programs in obesity care"}
    ) > _score_watch_item({"title": "Lifestyle nutrition programs in obesity care"})
