from nutev.global_watch.watch_capture import capture_watch_items, save_capture_json
from nutev.global_watch.watch_html_extract import extract_clean_html_text
from nutev.settings import NutevSettings
from nutev.logs import setup_logger


def _s(tmp_path):
    s = NutevSettings(project_root=tmp_path)
    for d in s.output_dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return s


def test_pdf_keeps_pdf_status(tmp_path, monkeypatch):
    class R:
        status_code = 200
        headers = {"Content-Type": "application/pdf"}
        content = b"%PDF-1.7 abc"
        text = ""
        url = "https://x/a.pdf"

    monkeypatch.setattr("requests.get", lambda *a, **k: R())
    s = _s(tmp_path)
    rows, _ = capture_watch_items(
        [{"document_id": "d1", "url": "https://x/a.pdf", "title": "x"}],
        s,
        setup_logger(s.output_dirs["07_logs"]),
        "run1",
        "quick",
    )
    assert rows[0]["download_status"] == "pdf"


def test_html_keeps_html_snapshot_status(tmp_path, monkeypatch):
    class R:
        status_code = 200
        headers = {"Content-Type": "text/html"}
        content = b"<html><title>T</title><h1>H</h1><body>Body</body></html>"
        text = "<html><title>T</title><h1>H</h1><body>Body</body></html>"
        url = "https://x/a"

    monkeypatch.setattr("requests.get", lambda *a, **k: R())
    s = _s(tmp_path)
    rows, _ = capture_watch_items(
        [{"document_id": "d1", "url": "https://x/a", "title": "x"}],
        s,
        setup_logger(s.output_dirs["07_logs"]),
        "run1",
        "quick",
    )
    assert rows[0]["download_status"] == "html_snapshot"


def test_http_404_metadata_only(tmp_path, monkeypatch):
    class R:
        status_code = 404
        headers = {"Content-Type": "text/html"}
        content = b"x"
        text = "x"
        url = "https://x/a"

    monkeypatch.setattr("requests.get", lambda *a, **k: R())
    s = _s(tmp_path)
    rows, _ = capture_watch_items(
        [{"document_id": "d1", "url": "https://x/a", "title": "x"}],
        s,
        setup_logger(s.output_dirs["07_logs"]),
        "run1",
        "quick",
    )
    assert rows[0]["download_status"] == "metadata_only"


def test_save_capture_json_preserves_status(tmp_path):
    item = {"document_id": "d1", "download_status": "pdf", "capture_status": "pdf", "artifact_paths": {}}
    out = save_capture_json(item, tmp_path)
    assert out["download_status"] == "pdf"


def test_capture_limit_override(tmp_path):
    s = _s(tmp_path)
    items = [{"document_id": f"d{i}", "url": ""} for i in range(25)]
    _, cap = capture_watch_items(items, s, setup_logger(s.output_dirs["07_logs"]), "run1", "quick", capture_limit=5)
    assert len(cap) == 5


def test_synthetic_fallback_never_captures(tmp_path, monkeypatch):
    def fail_requests(*args, **kwargs):
        raise AssertionError("requests.get should not be called for fallback.local")

    monkeypatch.setattr("requests.get", fail_requests)
    s = _s(tmp_path)
    rows, _ = capture_watch_items(
        [{"document_id": "d1", "url": "https://fallback.local", "title": "fallback", "source_provider": "watch_seed"}],
        s,
        setup_logger(s.output_dirs["07_logs"]),
        "run1",
        "quick",
    )
    assert rows[0]["download_status"] == "metadata_only"
    assert rows[0]["failure_reason"] == "synthetic_fallback_no_capture"


def test_html_extractor_removes_script_style():
    d = extract_clean_html_text('<html><head><style>x</style><script>y</script><title>T</title></head><body><h1>H</h1><a href="/x.pdf">pdf</a></body></html>')
    assert "script" not in d["clean_text"].lower() and d["title"] == "T"


def test_html_extractor_detects_title_headings_pdf_links():
    d = extract_clean_html_text('<html><title>ABC</title><body><h2>H2</h2><a href="/paper.pdf">p</a></body></html>')
    assert d["title"] == "ABC" and d["headings"] and d["pdf_links_found"]
