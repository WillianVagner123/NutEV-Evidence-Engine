from nutev.global_watch.watch_scoring import score_watch_item


def test_guideline_scores_above_editorial():
    assert score_watch_item({"title":"new guideline", "relevance_score":1, "is_new":True}) > score_watch_item({"title":"editorial note", "relevance_score":1})


def test_food_based_guideline_and_nutrition_literacy_score_above_editorial():
    assert score_watch_item({"title":"food-based dietary guideline for nutrition literacy and meal planning", "relevance_score":1, "is_new":True}) > score_watch_item({"title":"editorial note on laboratory methods", "relevance_score":1})
