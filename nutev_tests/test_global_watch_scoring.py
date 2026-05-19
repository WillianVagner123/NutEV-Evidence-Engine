from nutev.global_watch.watch_scoring import score_watch_item


def test_guideline_scores_above_editorial():
    assert score_watch_item({"title": "new guideline", "relevance_score": 1, "is_new": True}) > score_watch_item({"title": "editorial note", "relevance_score": 1})


def test_food_based_guideline_and_nutrition_literacy_score_above_editorial():
    assert score_watch_item({"title": "food-based dietary guideline for nutrition literacy and meal planning", "relevance_score": 1, "is_new": True}) > score_watch_item({"title": "editorial note on laboratory methods", "relevance_score": 1})


def test_best_practice_advice_and_scoping_review_score_above_generic_note():
    assert score_watch_item({"title": "best practice advice and scoping review for lifestyle nutrition care", "relevance_score": 1, "is_new": True}) > score_watch_item({"title": "generic nutrition note", "relevance_score": 1})


def test_masld_and_dyslipidaemia_terms_score_above_generic_note():
    assert score_watch_item({"title": "metabolic dysfunction-associated steatotic liver disease and dyslipidaemia guideline", "relevance_score": 1, "is_new": True}) > score_watch_item({"title": "generic nutrition note", "relevance_score": 1})


def test_hyperlipidemia_and_hypercholesterolemia_terms_score_above_generic_note():
    assert score_watch_item({"title": "hyperlipidemia and hypercholesterolemia guideline for cardiometabolic risk", "relevance_score": 1, "is_new": True}) > score_watch_item({"title": "generic nutrition note", "relevance_score": 1})


def test_living_systematic_review_scores_above_generic_note():
    assert score_watch_item({"title": "living systematic review of DASH adherence in primary care", "relevance_score": 1, "is_new": True}) > score_watch_item({"title": "generic nutrition note", "relevance_score": 1})
