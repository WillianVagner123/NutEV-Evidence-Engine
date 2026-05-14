from nutev.global_watch.watch_digest import write_digest

def test_digest_markdown_created(tmp_path):
    run_dir = tmp_path / "run"
    latest = tmp_path / "latest.md"
    md, _ = write_digest([{"title":"x","url":"u","download_status":"metadata_only"}], run_dir, latest)
    assert md.exists() and latest.exists()
