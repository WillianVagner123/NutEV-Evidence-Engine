from __future__ import annotations

import csv

from nutev.global_watch.watch_export import export_watch_outputs


def _read_header(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return next(csv.reader(handle))


def test_export_watch_outputs_writes_headers_for_empty_outputs(tmp_path) -> None:
    base_dir = tmp_path / "09_global_watch"
    run_dir = base_dir / "runs" / "2026-06-27"

    export_watch_outputs([], [], base_dir, run_dir)

    assert "document_id" in _read_header(base_dir / "global_watch_master.csv")
    assert "watch_score" in _read_header(run_dir / "global_watch_results.csv")
    assert _read_header(run_dir / "provider_performance.csv") == [
        "provider",
        "hits",
        "captured",
    ]
    assert _read_header(run_dir / "host_failures.csv") == [
        "host",
        "failure_reason",
        "http_status",
    ]
    assert _read_header(run_dir / "capture_manifest.csv") == [
        "artifact_paths",
        "capture_status",
        "document_id",
        "download_status",
    ]
