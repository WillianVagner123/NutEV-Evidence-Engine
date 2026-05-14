from nutev.global_watch.watch_export import export_watch_outputs

def test_exports_csv_created(tmp_path):
    export_watch_outputs([{"document_id":"d1"}], [{"document_id":"d1"}], tmp_path / "base", tmp_path / "run")
    assert (tmp_path / "base" / "global_watch_master.csv").exists()
