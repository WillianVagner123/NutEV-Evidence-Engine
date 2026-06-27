import csv
from collections.abc import Iterable


WATCH_OUTPUT_FIELDS = [
    "abstract",
    "artifact_paths",
    "capture_status",
    "category",
    "document_id",
    "doi",
    "download_status",
    "evidence_type",
    "failure_reason",
    "fallback_used",
    "final_url",
    "host",
    "http_status",
    "is_new",
    "is_new_to_system",
    "is_recent_publication",
    "matched_categories",
    "matched_providers",
    "novelty_score",
    "query",
    "relevance_score",
    "snippet",
    "source_provider",
    "title",
    "url",
    "watch_score",
    "webhook_included",
    "workstream_affinity",
    "year",
]

PROVIDER_PERFORMANCE_FIELDS = ["provider", "hits", "captured"]

HOST_FAILURE_FIELDS = ["host", "failure_reason", "http_status"]

CAPTURE_MANIFEST_FIELDS = [
    "artifact_paths",
    "capture_status",
    "document_id",
    "download_status",
]


def _fieldnames(rows: Iterable[dict], fallback_fields: list[str]) -> list[str]:
    discovered = sorted({key for row in rows for key in row.keys()})
    return discovered or fallback_fields


def _write_csv(rows, path, fallback_fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows or [])
    keys = _fieldnames(rows, list(fallback_fields or []))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def export_watch_outputs(
    rows,
    new_rows,
    base_dir,
    run_dir,
    provider_perf=None,
    host_failures=None,
    capture_manifest=None,
):
    _write_csv(rows, base_dir / "global_watch_master.csv", WATCH_OUTPUT_FIELDS)
    _write_csv(new_rows, base_dir / "global_watch_new_items.csv", WATCH_OUTPUT_FIELDS)
    _write_csv(rows, run_dir / "global_watch_results.csv", WATCH_OUTPUT_FIELDS)
    _write_csv(new_rows, run_dir / "global_watch_new_items.csv", WATCH_OUTPUT_FIELDS)
    _write_csv(
        provider_perf or [],
        run_dir / "provider_performance.csv",
        PROVIDER_PERFORMANCE_FIELDS,
    )
    _write_csv(host_failures or [], run_dir / "host_failures.csv", HOST_FAILURE_FIELDS)
    _write_csv(
        capture_manifest or [],
        run_dir / "capture_manifest.csv",
        CAPTURE_MANIFEST_FIELDS,
    )
