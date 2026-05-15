from nutev.engine.events import emit_event, load_events, write_event


def test_run_event_jsonl(tmp_path):
    path = tmp_path / "run_events.jsonl"
    ev = emit_event("run_1", "discovery_started", "ok")
    write_event(ev, path)
    loaded = load_events(path)
    assert loaded and loaded[0].run_id == "run_1"
