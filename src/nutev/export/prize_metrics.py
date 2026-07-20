from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger("nutev.export.prize_metrics")


TRUE_VALUES = {"true", "1", "yes", "sim", "ok", "used", "pdf", "html_snapshot", "success"}
IDENTIFIER_COLUMNS = ["doi", "pmid", "pmcid", "url", "final_url", "original_url", "title", "year"]
SOURCE_COLUMNS = ["source", "source_provider", "provider", "source_institution"]
DOMAIN_PREFIXES = ("domain_", "lens_", "outcome_")


def _read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _read_xlsx_safe(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(path)
    except Exception:
        return pd.DataFrame()


def _read_json_safe(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        # Present-but-malformed input would otherwise show as silent zeros.
        logger.warning("metrics input unreadable, treated as empty: path=%s error=%s", path, exc)
        return {}


def _boolish(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin(TRUE_VALUES)


def _value_counts(df: pd.DataFrame, column: str, limit: int = 20) -> dict[str, int]:
    if df.empty or column not in df.columns:
        return {}
    counts = df[column].fillna("missing").astype(str).str.strip().replace("", "missing").value_counts().head(limit)
    return {str(k): int(v) for k, v in counts.items()}


def _unique_document_count(metadata: pd.DataFrame) -> int:
    if metadata.empty:
        return 0
    key_cols = [c for c in IDENTIFIER_COLUMNS if c in metadata.columns]
    if not key_cols:
        return int(metadata.drop_duplicates().shape[0])

    normalized = metadata[key_cols].copy()
    for col in normalized.columns:
        normalized[col] = normalized[col].fillna("").astype(str).str.strip().str.lower()

    # Prefer bibliographic identifiers; fallback to title/year or any available operational key.
    for cols in (["doi"], ["pmid"], ["pmcid"], ["final_url"], ["url"], ["original_url"], ["title", "year"]):
        existing = [c for c in cols if c in normalized.columns]
        if len(existing) != len(cols):
            continue
        subset = normalized[existing]
        mask = subset.apply(lambda row: any(bool(x) for x in row), axis=1)
        if mask.any():
            return int(subset[mask].drop_duplicates().shape[0] + (~mask).sum())

    return int(normalized.drop_duplicates().shape[0])


def _collect_analysis_tables(tables_dir: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for file in sorted(tables_dir.glob("analysis_*.xlsx")):
        df = _read_xlsx_safe(file)
        if not df.empty:
            df["analysis_file"] = file.name
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _extract_domain_counts(df: pd.DataFrame, limit: int = 30) -> dict[str, int]:
    if df.empty:
        return {}

    counts: dict[str, int] = {}

    for col in df.columns:
        if col.startswith(DOMAIN_PREFIXES):
            try:
                counts[col] = int(_boolish(df[col]).sum())
            except Exception:
                continue

    if "domains" in df.columns:
        exploded = (
            df["domains"]
            .dropna()
            .astype(str)
            .str.replace("[", "", regex=False)
            .str.replace("]", "", regex=False)
            .str.replace("'", "", regex=False)
            .str.replace('"', "", regex=False)
            .str.split(r"[;,|]", regex=True)
            .explode()
            .str.strip()
        )
        for name, value in exploded.value_counts().head(limit).items():
            if name:
                counts[f"domains::{name}"] = int(value)

    return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit])


def _load_existing_run_summary(root: Path) -> dict[str, Any]:
    return _read_json_safe(root / "07_logs" / "run_summary.json")


def build_prize_metrics_summary(project_root: Path) -> dict[str, Any]:
    root = Path(project_root)

    metadata = _read_csv_safe(root / "02_metadata" / "metadata_master.csv")
    rayyan = _read_csv_safe(root / "02_metadata" / "rayyan_ready.csv")
    downloads = _read_csv_safe(root / "03_corpus" / "download_manifest.csv")
    failed = _read_csv_safe(root / "03_corpus" / "failed_downloads.csv")
    extraction = _read_csv_safe(root / "05_extraction" / "extraction_manifest.csv")
    analysis = _collect_analysis_tables(root / "06_tables")
    existing_summary = _load_existing_run_summary(root)

    summary: dict[str, Any] = {
        "project_root": str(root),
        "records_total": int(existing_summary.get("records", len(metadata))),
        "unique_documents_estimated": int(
            existing_summary.get("curated_unique_documents", _unique_document_count(metadata))
        ),
        "rayyan_records": int(len(rayyan)),
        "downloads_ok": int(existing_summary.get("downloads_ok", len(downloads))),
        "downloads_failed": int(existing_summary.get("downloads_failed", len(failed))),
        "extraction_records": int(len(extraction)),
        "ocr_docs": int(
            existing_summary.get(
                "ocr_docs",
                int(_boolish(extraction["used_ocr"]).sum()) if "used_ocr" in extraction.columns else 0,
            )
        ),
    }

    for key in (
        "evidence_claims_total",
        "evidence_claims_supported",
        "evidence_claims_needs_review",
        "recommendation_candidates_total",
        "recommendation_candidates_ready_review",
        "recommendation_candidates_insufficient_evidence",
        "conflicting_evidence_total",
    ):
        if key in existing_summary:
            summary[key] = existing_summary[key]

    if "workstream" in metadata.columns:
        summary["records_by_workstream"] = _value_counts(metadata, "workstream", limit=20)

    source_col = next((c for c in SOURCE_COLUMNS if c in metadata.columns), None)
    if source_col:
        summary["records_by_source"] = _value_counts(metadata, source_col, limit=20)

    if "extraction_status" in metadata.columns:
        summary["extraction_status"] = _value_counts(metadata, "extraction_status", limit=20)

    if "failure_reason" in metadata.columns:
        failure_counts = _value_counts(metadata[metadata["failure_reason"].fillna("").astype(str).str.strip() != ""], "failure_reason", limit=20)
        if failure_counts:
            summary["failure_reasons"] = failure_counts

    summary["top_domain_counts"] = _extract_domain_counts(analysis, limit=30)

    return summary


def write_prize_metrics_summary(project_root: Path) -> Path:
    root = Path(project_root)
    logs_dir = root / "07_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    summary = build_prize_metrics_summary(root)

    out_json = logs_dir / "prize_metrics_summary.json"
    out_txt = logs_dir / "prize_metrics_summary.txt"

    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = ["RESUMO NUMERICO PARA O PREMIO", ""]
    for key, value in summary.items():
        lines.append(f"{key}: {value}")
    out_txt.write_text("\n".join(lines), encoding="utf-8")

    return out_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Export NutEV prize metrics from a project_output folder.")
    parser.add_argument("--project-root", required=True, type=Path)
    args = parser.parse_args()

    out = write_prize_metrics_summary(args.project_root)
    print(out)
    print(out.with_suffix(".txt"))


if __name__ == "__main__":
    main()
