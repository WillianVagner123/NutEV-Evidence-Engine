from nutev.global_watch.watch_scoring import score_watch_item

def test_guideline_scores_above_editorial():
    assert score_watch_item({"title":"new guideline", "relevance_score":1, "is_new":True}) > score_watch_item({"title":"editorial note", "relevance_score":1})
