from nutev.global_watch.watch_query_builder import build_watch_queries

def test_build_watch_queries_generates_queries():
    rows = build_watch_queries(["guidelines_consensus"], 7, "quick")
    assert rows and "query_id" in rows[0]
