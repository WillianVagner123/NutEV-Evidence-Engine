from nutev.global_watch.watch_query_builder import build_watch_queries


def test_quick_mode_global_watch_covers_group_visit_delivery_models() -> None:
    rows = build_watch_queries(["lifestyle_medicine", "implementation_behavior"], 7, "quick")
    rendered = " ".join(str(row["query"]).lower() for row in rows)

    assert "group lifestyle intervention" in rendered
    assert "group nutrition counseling" in rendered
    assert "group dietitian visit" in rendered
    assert "group medical visit" in rendered
    assert "shared medical appointment" in rendered
    assert "obesity group visit" in rendered
