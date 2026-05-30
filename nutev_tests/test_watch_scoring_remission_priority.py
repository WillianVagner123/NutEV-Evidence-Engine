import importlib


def _score_watch_item(item: dict) -> float:
    module = importlib.import_module("nutev.global_watch.watch_scoring")
    return module.score_watch_item(item)


def test_diabetes_prevention_program_variants_improve_priority() -> None:
    assert _score_watch_item(
        {
            "title": "National Diabetes Prevention Programme lifestyle intervention for obesity care",
        }
    ) > _score_watch_item({"title": "Lifestyle intervention for obesity care"})


def test_diabetes_remission_diet_signals_improve_priority() -> None:
    assert _score_watch_item(
        {
            "title": "Total diet replacement and very low energy diet for type 2 diabetes remission",
        }
    ) > _score_watch_item({"title": "Type 2 diabetes remission note"})
