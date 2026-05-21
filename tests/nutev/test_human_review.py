from pathlib import Path
from nutev.review.human_review import append_human_review_decision, load_human_review_decisions


def test_human_review_append_without_overwrite(tmp_path: Path):
    append_human_review_decision(tmp_path, {
        'item_type':'claim','item_id':'c1','reviewer_name':'A','reviewer_role':'reviewer_1','reviewer_decision':'approve','reviewer_notes':'ok','final_decision':'approved'
    })
    append_human_review_decision(tmp_path, {
        'item_type':'claim','item_id':'c1','reviewer_name':'B','reviewer_role':'reviewer_2','reviewer_decision':'needs_second_reviewer','reviewer_notes':'check','final_decision':'pending'
    })
    df = load_human_review_decisions(tmp_path)
    assert len(df) == 2
