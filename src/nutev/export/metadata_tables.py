from __future__ import annotations

import csv
from pathlib import Path

REQUIRED_METADATA_COLUMNS = [
    "document_id", "title", "doi", "pmid", "pmcid", "original_url", "final_url", "source_provider", "source_institution",
    "country", "region", "workstream", "year", "language", "evidence_type", "capture_status", "download_status", "extraction_status",
    "artifact_paths", "failure_reason", "relevance_score", "novelty_score", "domains", "outcomes", "diet_patterns", "clinical_conditions",
    "first_seen_date", "last_seen_date", "is_new", "llm_decision", "llm_reason",
]

KNOWN_SIMPLE_CSV_COLUMNS = {
    "download_manifest.csv": [
        "url",
        "resolved_url",
        "path",
        "ext",
        "source",
        "status",
    ],
    "failed_downloads.csv": [
        "url",
        "resolved_url",
        "status",
        "reason",
        "head_status",
        "document_id",
    ],
    "extraction_manifest.csv": [
        "file",
        "ext",
        "used_ocr",
        "ocr_failed_pages",
        "text_path",
        "chars",
        "extraction_status",
    ],
    "dedup_manifest.csv": [
        "workstream",
        "document_key",
        "document_key_type",
        "dedup_rule",
        "occurrence_role",
        "input_index",
        "winner_input_index",
        "absorbed_count",
        "merge_reason",
        "winner_url_after_merge",
        "occurrence_url",
        "source",
        "source_provider",
        "title",
        "doi",
        "pmid",
        "pmcid",
        "year",
    ],
    "querypack_executed.csv": [
        "workstream",
        "query_order",
        "query_text",
    ],
    "provider_querypack_executed.csv": [
        "workstream",
        "provider",
        "query_order",
        "query_text",
    ],
}


def _normalize_metadata_row(row: dict) -> dict:
    out = {k: row.get(k, "") for k in REQUIRED_METADATA_COLUMNS}
    out["document_id"] = row.get("document_id") or row.get("id") or ""
    out["title"] = row.get("title", "")
    out["doi"] = row.get("doi", "")
    out["original_url"] = row.get("original_url", row.get("url", ""))
    out["final_url"] = row.get("final_url", row.get("resolved_url", row.get("url", "")))
    out["artifact_paths"] = row.get("artifact_paths", row.get("file_path", ""))
    out["capture_status"] = row.get("capture_status", "missing")
    out["download_status"] = row.get("download_status", "metadata_only" if not row.get("file_path") else "pdf")
    out["extraction_status"] = row.get("extraction_status", "missing")
    return out


def write_metadata_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata_rows = [_normalize_metadata_row(r) for r in rows]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=REQUIRED_METADATA_COLUMNS)
        w.writeheader()
        w.writerows(metadata_rows)


def write_simple_csv(
    rows: list[dict], path: Path, fieldnames: list[str] | None = None
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = fieldnames or KNOWN_SIMPLE_CSV_COLUMNS.get(path.name)
    if rows:
        row_keys = sorted({k for r in rows for k in r.keys()})
        keys = list(dict.fromkeys((keys or []) + row_keys))
    if not keys:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        if rows:
            w.writerows(rows)
