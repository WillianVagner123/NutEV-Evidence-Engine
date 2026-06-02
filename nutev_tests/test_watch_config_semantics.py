from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_watch_config_includes_diabetes_remission_and_reversal_terms():
    terms = {term.lower() for term in WATCH_CATEGORIES["obesity_cardiometabolic"]}

    assert "type 2 diabetes remission" in terms
    assert "remission of type 2 diabetes" in terms
    assert "type 2 diabetes reversal" in terms
    assert "diabetes reversal" in terms
    assert "glycemic remission" in terms
    assert "glycaemic remission" in terms


def test_watch_config_includes_low_energy_total_diet_replacement_terms():
    terms = {term.lower() for term in WATCH_CATEGORIES["diet_patterns"]}

    assert "total diet replacement" in terms
    assert "low-calorie total diet replacement" in terms
    assert "low calorie total diet replacement" in terms
    assert "very low energy diet" in terms
    assert "low-calorie diet" in terms
