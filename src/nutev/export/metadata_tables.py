from __future__ import annotations
import csv
from pathlib import Path

REQUIRED_METADATA_COLUMNS = [
    "document_id",
    "title",
    "doi",
    "pmid",
    "pmcid",
    "original_url",
    "final_url",
    "source_provider",
    "source_institution",
    "country",
    "region",
    "workstream",
    "year",
    "language",
    "evidence_type",
    "capture_status",
    "download_status",
    "extraction_status",
    "ocr_status",
    "ocr_attempted",
    "used_ocr",
    "ocr_failed_pages",
    "extraction_failure_reason",
    "artifact_paths",
    "failure_reason",
    "relevance_score",
    "novelty_score",
    "domains",
    "outcomes",
    "diet_patterns",
    "clinical_conditions",
    "first_seen_date",
    "last_seen_date",
    "is_new",
    "llm_decision",
    "llm_reason",
]


def _normalize_metadata_row(row: dict) -> dict:
    out = {key: row.get(key, "") for key in REQUIRED_METADATA_COLUMNS}
    out["document_id"] = row.get("document_id") or row.get("id") or ""
    out["title"] = row.get("title", "")
    out["doi"] = row.get("doi", "")
    out["original_url"] = row.get("original_url", row.get("url", ""))
    out["final_url"] = row.get("final_url", row.get("resolved_url", row.get("url", "")))
    out["artifact_paths"] = row.get("artifact_paths", row.get("file_path", ""))
    out["capture_status"] = row.get("capture_status", "missing")
    out["download_status"] = row.get(
        "download_status",
        "metadata_only" if not row.get("file_path") else "pdf",
    )
    out["extraction_status"] = row.get("extraction_status", "missing")
    out["ocr_status"] = row.get("ocr_status", "not_used")
    out["ocr_attempted"] = row.get("ocr_attempted", "")
    out["used_ocr"] = row.get("used_ocr", "")
    out["ocr_failed_pages"] = row.get("ocr_failed_pages", "")
    out["extraction_failure_reason"] = row.get("extraction_failure_reason", "")
    out["failure_reason"] = row.get("failure_reason", row.get("extraction_failure_reason", ""))
    return out


def write_metadata_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata_rows = [_normalize_metadata_row(row) for row in rows]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_METADATA_COLUMNS)
        writer.writeheader()
        writer.writerows(metadata_rows)


def write_simple_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({key for row in rows for key in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
