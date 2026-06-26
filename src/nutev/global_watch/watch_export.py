import csv
from pathlib import Path
from collections.abc import Iterable, Sequence

WATCH_OUTPUT_COLUMNS = [
    "title",
    "abstract",
    "snippet",
    "url",
    "doi",
    "year",
    "source_provider",
    "category",
    "query",
    "evidence_type",
    "workstream_affinity",
    "matched_categories",
    "matched_providers",
    "download_status",
    "relevance_score",
    "watch_score",
    "failure_reason",
    "fallback_used",
    "is_recent_publication",
    "is_new",
    "document_id",
]

PROVIDER_PERFORMANCE_COLUMNS = [
    "run_id",
    "provider",
    "workstream",
    "query_hash",
    "query",
    "status",
    "total_found",
    "rows_returned",
    "duration_seconds",
    "resume_used",
    "checkpoint_path",
]

HOST_FAILURE_COLUMNS = [
    "host",
    "url",
    "status",
    "reason",
    "attempted_at",
]

CAPTURE_MANIFEST_COLUMNS = [
    "document_id",
    "title",
    "url",
    "status",
    "capture_status",
    "download_status",
    "artifact_path",
    "failure_reason",
]


def _fieldnames(rows: Sequence[dict], default_fields: Iterable[str]) -> list[str]:
    keys = sorted({key for row in rows for key in row.keys()})
    default = [field for field in default_fields if field]
    merged = default + [key for key in keys if key not in default]
    return merged or keys


def _write_csv(rows, path: Path, default_fields: Iterable[str] = ()):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows or [])
    keys = _fieldnames(rows, default_fields)
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
    _write_csv(rows, base_dir / "global_watch_master.csv", WATCH_OUTPUT_COLUMNS)
    _write_csv(new_rows, base_dir / "global_watch_new_items.csv", WATCH_OUTPUT_COLUMNS)
    _write_csv(rows, run_dir / "global_watch_results.csv", WATCH_OUTPUT_COLUMNS)
    _write_csv(new_rows, run_dir / "global_watch_new_items.csv", WATCH_OUTPUT_COLUMNS)
    _write_csv(
        provider_perf or [],
        run_dir / "provider_performance.csv",
        PROVIDER_PERFORMANCE_COLUMNS,
    )
    _write_csv(host_failures or [], run_dir / "host_failures.csv", HOST_FAILURE_COLUMNS)
    _write_csv(
        capture_manifest or [],
        run_dir / "capture_manifest.csv",
        CAPTURE_MANIFEST_COLUMNS,
    )
