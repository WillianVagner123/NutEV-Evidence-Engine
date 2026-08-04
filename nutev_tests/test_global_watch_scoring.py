from nutev.global_watch.watch_scoring import score_watch_item


def test_guideline_scores_above_editorial():
    assert score_watch_item({"title": "new guideline", "relevance_score": 1, "is_new": True}) > score_watch_item({"title": "editorial note", "relevance_score": 1})


def test_food_based_guideline_and_nutrition_literacy_score_above_editorial():
    assert score_watch_item({"title": "food-based dietary guideline for nutrition literacy and meal planning", "relevance_score": 1, "is_new": True}) > score_watch_item({"title": "editorial note on laboratory methods", "relevance_score": 1})


def test_teaching_kitchen_and_culinary_nutrition_score_above_generic_note():
    assert score_watch_item({"title": "teaching kitchen and culinary nutrition intervention for food literacy", "relevance_score": 1, "is_new": True}) > score_watch_item({"title": "generic nutrition note", "relevance_score": 1})


def test_masld_and_dyslipidaemia_terms_score_above_generic_note():
    assert score_watch_item({"title": "metabolic dysfunction-associated steatotic liver disease and dyslipidaemia guideline", "relevance_score": 1, "is_new": True}) > score_watch_item({"title": "generic nutrition note", "relevance_score": 1})


def test_metabolic_dysfunction_associated_steatohepatitis_terms_score_above_generic_note():
    assert score_watch_item({"title": "metabolic dysfunction-associated steatohepatitis nutrition guideline", "relevance_score": 1, "is_new": True}) > score_watch_item({"title": "generic nutrition note", "relevance_score": 1})


def test_hyperlipidemia_and_hypercholesterolemia_terms_score_above_generic_note():
    assert score_watch_item({"title": "hyperlipidemia and hypercholesterolemia guideline for cardiometabolic risk", "relevance_score": 1, "is_new": True}) > score_watch_item({"title": "generic nutrition note", "relevance_score": 1})


def test_central_adiposity_terms_score_above_generic_note():
    assert score_watch_item({"title": "central obesity and waist circumference intervention for cardiometabolic health", "relevance_score": 1, "is_new": True}) > score_watch_item({"title": "generic nutrition note", "relevance_score": 1})


def test_diabetes_remission_terms_score_above_generic_note():
    assert score_watch_item({"title": "type 2 diabetes remission after medical nutrition therapy", "relevance_score": 1, "is_new": True}) > score_watch_item({"title": "generic nutrition note", "relevance_score": 1})


def test_adherence_and_behavior_instruments_score_above_generic_note():
    instrument_item = {
        "title": "dietary adherence questionnaire and eating behavior questionnaire validation",
        "abstract": "self-efficacy scale for meal planning and nutrition behavior",
        "relevance_score": 1,
        "is_new": True,
    }
    assert score_watch_item(instrument_item) > score_watch_item({"title": "generic nutrition note", "relevance_score": 1})


def test_sustainable_healthy_diet_guidance_scores_above_generic_note():
    item = {
        "title": "Sustainable healthy diet guideline for cardiometabolic nutrition",
        "relevance_score": 1,
        "is_new": True,
    }
    assert score_watch_item(item) > score_watch_item({"title": "generic nutrition note", "relevance_score": 1})
