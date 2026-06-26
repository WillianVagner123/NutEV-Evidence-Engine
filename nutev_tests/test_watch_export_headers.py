from __future__ import annotations

import csv

from nutev.global_watch.watch_export import export_watch_outputs


def _headers(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return next(csv.reader(handle))


def test_export_watch_outputs_writes_headers_for_empty_csvs(tmp_path) -> None:
    base_dir = tmp_path / "09_global_watch"
    run_dir = base_dir / "runs" / "run_empty"

    export_watch_outputs([], [], base_dir, run_dir)

    watch_headers = _headers(base_dir / "global_watch_master.csv")
    assert "document_id" in watch_headers
    assert "title" in watch_headers
    assert "source_provider" in watch_headers
    assert "workstream_affinity" in watch_headers

    assert _headers(base_dir / "global_watch_new_items.csv") == watch_headers
    assert _headers(run_dir / "global_watch_results.csv") == watch_headers
    assert _headers(run_dir / "global_watch_new_items.csv") == watch_headers

    provider_headers = _headers(run_dir / "provider_performance.csv")
    assert "provider" in provider_headers
    assert "query_hash" in provider_headers
    assert "rows_returned" in provider_headers

    host_failure_headers = _headers(run_dir / "host_failures.csv")
    assert "host" in host_failure_headers
    assert "reason" in host_failure_headers

    capture_headers = _headers(run_dir / "capture_manifest.csv")
    assert "document_id" in capture_headers
    assert "capture_status" in capture_headers
    assert "failure_reason" in capture_headers
