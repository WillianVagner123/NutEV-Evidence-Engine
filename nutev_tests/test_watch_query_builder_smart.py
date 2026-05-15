from nutev.global_watch.watch_query_builder import build_watch_queries


def test_watch_queries_have_intent_and_affinity():
    rows=build_watch_queries([],7,'quick')
    assert rows and 'intent' in rows[0] and 'workstream_affinity' in rows[0]
