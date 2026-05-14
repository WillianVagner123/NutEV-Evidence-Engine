from nutev.global_watch.watch_diff import mark_new_items

def test_mark_new_items():
    rows = mark_new_items([{"document_id":"doc1"}], {})
    assert rows[0]["is_new"] is True
