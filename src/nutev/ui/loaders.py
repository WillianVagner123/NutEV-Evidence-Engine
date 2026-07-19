from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def empty_with_warning(warning: str = "not available yet"):
    return pd.DataFrame(), warning


def load_csv(path: Path):
    if not path.exists():
        return empty_with_warning()
    try:
        return pd.read_csv(path), "ok"
    except Exception as e:
        return empty_with_warning(f"not available yet: {e}")


def load_xlsx_or_csv(xlsx_path: Path, csv_path: Path | None = None):
    if xlsx_path.exists():
        try:
            data = pd.read_excel(xlsx_path, sheet_name=0)
            if isinstance(data, dict):
                data = next(iter(data.values())) if data else pd.DataFrame()
            return data, "ok"
        except Exception:
            import logging

            logging.getLogger(__name__).debug("xlsx read failed, falling back to csv: %s", xlsx_path, exc_info=True)
    if csv_path and csv_path.exists():
        return load_csv(csv_path)
    return empty_with_warning()


def load_json_file(path: Path):
    if not path.exists():
        return {}, "not available yet"
    try:
        return json.loads(path.read_text(encoding="utf-8")), "ok"
    except Exception as e:
        return {}, f"not available yet: {e}"


def load_jsonl(path: Path):
    if not path.exists():
        return empty_with_warning()
    rows = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return pd.DataFrame(rows), "ok"
    except Exception as e:
        return empty_with_warning(f"not available yet: {e}")


def normalize_bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "yes", "y", "sim"])


def list_export_artifacts(project_root: Path) -> pd.DataFrame:
    paths = [
        "02_metadata/metadata_master.csv",
        "02_metadata/NUTEV_EVIDENCE_CLAIMS.csv",
        "02_metadata/NUTEV_RECOMMENDATION_CANDIDATES.csv",
        "02_metadata/NUTEV_REFERENCES.bib",
        "02_metadata/NUTEV_REFERENCES.ris",
        "06_tables/NUTEV_GLOBAL_EVIDENCE_MATRIX.xlsx",
        "06_tables/NUTEV_PROTOCOL_TRANSLATION_MATRIX.xlsx",
        "06_tables/NUTEV_EVIDENCE_CLAIMS.xlsx",
        "06_tables/NUTEV_RECOMMENDATION_CANDIDATES.xlsx",
        "06_tables/NUTEV_HUMAN_REVIEW_QUEUE.xlsx",
        "06_tables/NUTEV_EVIDENCE_CONVERGENCE_MATRIX.xlsx",
        "06_tables/NUTEV_PROTOCOL_READINESS_MATRIX.xlsx",
        "06_tables/NUTEV_EVIDENCE_GAP_REGISTER.xlsx",
        "08_docs/NUTEV_METHODS_MASTER.md",
        "08_docs/NUTEV_PILOT_REPORT.md",
        "08_docs/NUTEV_SCIENTIFIC_RIGOR_REPORT.md",
        "07_logs/run_summary.json",
        "07_logs/human_review_decisions.csv",
    ]
    rows: list[dict[str, Any]] = []
    for rel in paths:
        path = project_root / rel
        rows.append({"artifact": path.name, "relative_path": rel, "status": "available" if path.exists() else "missing", "size_bytes": path.stat().st_size if path.exists() else 0})
    return pd.DataFrame(rows)


def calculate_overview_metrics(run_summary: dict, metadata: pd.DataFrame, claims: pd.DataFrame, recs: pd.DataFrame) -> dict[str, int]:
    if run_summary:
        return {
            "total_records": int(run_summary.get("total_records", run_summary.get("records", 0)) or 0),
            "downloaded_documents": int(run_summary.get("downloaded_documents", run_summary.get("downloads_ok", 0)) or 0),
            "metadata_only_records": int(run_summary.get("metadata_only_records", run_summary.get("downloads_failed", 0)) or 0),
            "extracted_texts": int(run_summary.get("extracted_texts", run_summary.get("ocr_docs", 0)) or 0),
            "evidence_claims_total": int(run_summary.get("evidence_claims_total", 0) or 0),
            "evidence_claims_supported": int(run_summary.get("evidence_claims_supported", 0) or 0),
            "evidence_claims_needs_review": int(run_summary.get("evidence_claims_needs_review", 0) or 0),
            "recommendation_candidates_total": int(run_summary.get("recommendation_candidates_total", 0) or 0),
            "recommendation_candidates_ready_review": int(run_summary.get("recommendation_candidates_ready_review", 0) or 0),
            "recommendation_candidates_insufficient_evidence": int(run_summary.get("recommendation_candidates_insufficient_evidence", 0) or 0),
            "conflicting_evidence_total": int(run_summary.get("conflicting_evidence_total", 0) or 0),
            "protocol_ready_total": int(run_summary.get("protocol_ready_total", 0) or 0),
            "evidence_gaps_total": int(run_summary.get("evidence_gaps_total", 0) or 0),
            "adjudication_queue_total": int(run_summary.get("adjudication_queue_total", 0) or 0),
        }
    return {
        "total_records": int(len(metadata)),
        "downloaded_documents": int((metadata.get("download_status", pd.Series(dtype=str)).astype(str) == "pdf").sum()) if not metadata.empty else 0,
        "metadata_only_records": int((metadata.get("download_status", pd.Series(dtype=str)).astype(str) == "metadata_only").sum()) if not metadata.empty else 0,
        "extracted_texts": int(metadata.get("extraction_status", pd.Series(dtype=str)).astype(str).isin(["ok", "ok_ocr", "fake_pdf_html", "fake_pdf_text"]).sum()) if not metadata.empty else 0,
        "evidence_claims_total": int(len(claims)),
        "evidence_claims_supported": int((claims.get("claim_status", pd.Series(dtype=str)).astype(str) == "supported").sum()) if not claims.empty else 0,
        "evidence_claims_needs_review": int(normalize_bool_series(claims.get("needs_human_review", pd.Series(dtype=str))).sum()) if not claims.empty else 0,
        "recommendation_candidates_total": int(len(recs)),
        "recommendation_candidates_ready_review": int((recs.get("recommendation_status", pd.Series(dtype=str)).astype(str) == "ready_for_human_review").sum()) if not recs.empty else 0,
        "recommendation_candidates_insufficient_evidence": int((recs.get("recommendation_status", pd.Series(dtype=str)).astype(str) == "insufficient_evidence").sum()) if not recs.empty else 0,
        "conflicting_evidence_total": int((claims.get("claim_status", pd.Series(dtype=str)).astype(str) == "conflicting").sum()) if not claims.empty else 0,
        "protocol_ready_total": int((recs.get("readiness_class", pd.Series(dtype=str)).astype(str) == "protocol_ready").sum()) if not recs.empty else 0,
        "evidence_gaps_total": 0,
        "adjudication_queue_total": 0,
    }
