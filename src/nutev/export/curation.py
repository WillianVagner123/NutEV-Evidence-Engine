from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pandas as pd

from nutev.analysis.prisma import build_prisma_flow
from nutev.engine.ids import make_document_id
from nutev.engine.validators import normalize_doi
from nutev.export.excel_writer import write_excel_sheet

FULL_TEXT_EXTRACTION_STATUSES = {
    "ok",
    "ok_ocr",
    "ok_native_low_confidence",
    "fake_pdf_html",
    "fake_pdf_text",
}

CURATED_METADATA_COLUMNS = [
    "document_key",
    "document_id",
    "title",
    "workstream",
    "doi",
    "pmid",
    "pmcid",
    "year",
    "source",
    "source_provider",
    "url",
    "canonical_url",
    "file_path",
    "score",
    "domains",
    "nutev_objects",
    "ocr_status",
    "ocr_attempted",
    "used_ocr",
    "ocr_failed_pages",
    "extraction_status",
    "extraction_failure_reason",
    "is_full_text_available",
    "is_metadata_only",
]

UNIQUE_DOCUMENT_COLUMNS = [
    "document_key",
    "document_id",
    "title",
    "doi",
    "pmid",
    "pmcid",
    "year",
    "canonical_url",
    "source",
    "source_provider",
    "doc_type",
    "evidence_type",
    "score",
    "domains",
    "nutev_objects",
    "workstreams",
    "raw_occurrence_count",
    "workstream_count",
    "ocr_status",
    "ocr_attempted",
    "used_ocr",
    "ocr_failed_pages",
    "extraction_status",
    "extraction_failure_reason",
    "file_path",
    "is_full_text_available",
    "is_metadata_only",
]

WORKSTREAM_MAP_COLUMNS = [
    "document_key",
    "document_id",
    "workstream",
    "title",
    "canonical_url",
    "score_max",
    "raw_occurrence_count",
]


def _normalize_url(value: str | None) -> str:
    if not value:
        return ""
    parsed = urlparse(str(value).strip())
    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            "",
            parsed.query,
            "",
        )
    )


def _normalize_title(value: str | None) -> str:
    title = " ".join((value or "").lower().split())
    return "".join(char for char in title if char.isalnum() or char.isspace()).strip()


def _row_hash(row: dict) -> str:
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def build_document_key(row: dict) -> str:
    doi = normalize_doi(row.get("doi"))
    if doi:
        return f"doi:{doi}"

    pmid = str(row.get("pmid") or "").strip().lower()
    if pmid:
        return f"pmid:{pmid}"

    pmcid = str(row.get("pmcid") or "").strip().lower()
    if pmcid:
        return f"pmcid:{pmcid}"

    canonical_url = _normalize_url(
        row.get("final_url")
        or row.get("resolved_url")
        or row.get("url")
        or row.get("original_url")
    )
    if canonical_url:
        return f"url:{canonical_url}"

    normalized_title = _normalize_title(row.get("title"))
    year = str(row.get("year") or "").strip()
    if normalized_title:
        return f"title_year:{normalized_title}|{year}"

    return f"rowhash:{_row_hash(row)}"


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "sim", "used"}
    return bool(value)


def _as_float(value: object) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _canonical_domains(value: object) -> str:
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return ";".join(dict.fromkeys(items))
    text = str(value or "").strip()
    if not text:
        return ""
    items = [item.strip() for item in text.split(";") if item.strip()]
    return ";".join(dict.fromkeys(items))


def _normalized_ocr_status(row: dict) -> str:
    if _as_bool(row.get("used_ocr")):
        return "used"
    if row.get("extraction_status") == "ocr_unavailable":
        return "unavailable"
    if _as_bool(row.get("ocr_attempted")):
        return "attempted_without_text"
    return "not_needed"


def _is_full_text_available(row: dict) -> bool:
    if row.get("extraction_status") in FULL_TEXT_EXTRACTION_STATUSES:
        return True
    return bool(str(row.get("file_path") or "").strip()) and row.get("extraction_status") not in {
        "missing",
        "empty",
        "pdf_no_text",
        "ocr_unavailable",
        "ocr_fail",
    }


def _representative_sort_key(row: dict) -> tuple[int, float, int, str]:
    return (
        int(_is_full_text_available(row)),
        _as_float(row.get("score") or row.get("relevance_score")),
        int(_as_bool(row.get("used_ocr"))),
        str(row.get("title") or ""),
    )


def _frame(rows: list[dict], columns: list[str]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=columns)
    for column in columns:
        if column not in df.columns:
            df[column] = ""
    return df.loc[:, columns]


def _enrich_rows(all_rows: list[dict], extraction_manifest: list[dict]) -> list[dict]:
    extraction_by_file = {
        str(item.get("file") or ""): item
        for item in extraction_manifest
        if str(item.get("file") or "")
    }
    enriched: list[dict] = []

    for row in all_rows:
        item = dict(row)
        file_path = str(item.get("file_path") or "")
        extraction = extraction_by_file.get(file_path, {})
        canonical_url = _normalize_url(
            item.get("final_url")
            or item.get("resolved_url")
            or item.get("url")
            or item.get("original_url")
        )

        item["document_id"] = item.get("document_id") or make_document_id(item)
        item["document_key"] = build_document_key(item)
        item["canonical_url"] = canonical_url
        item["source"] = item.get("source") or item.get("source_provider") or ""
        item["source_provider"] = item.get("source_provider") or item.get("source") or ""
        item["score"] = _as_float(item.get("score") or item.get("relevance_score"))
        item["domains"] = _canonical_domains(item.get("domains"))
        item["nutev_objects"] = _canonical_domains(item.get("nutev_objects"))
        item["ocr_attempted"] = _as_bool(item.get("ocr_attempted") or extraction.get("ocr_attempted"))
        item["used_ocr"] = _as_bool(item.get("used_ocr") or extraction.get("used_ocr"))
        item["ocr_failed_pages"] = item.get("ocr_failed_pages") or extraction.get("ocr_failed_pages") or ""
        item["extraction_status"] = item.get("extraction_status") or extraction.get("extraction_status") or "missing"
        item["extraction_failure_reason"] = item.get("extraction_failure_reason") or extraction.get("failure_reason") or ""
        item["ocr_status"] = _normalized_ocr_status(item)
        item["is_full_text_available"] = _is_full_text_available(item)
        item["is_metadata_only"] = not item["is_full_text_available"]
        item["file_path"] = file_path
        enriched.append(item)

    return enriched


def _build_unique_documents(enriched_rows: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not enriched_rows:
        return (
            _frame([], CURATED_METADATA_COLUMNS),
            _frame([], UNIQUE_DOCUMENT_COLUMNS),
            _frame([], WORKSTREAM_MAP_COLUMNS),
        )

    metadata_df = _frame(enriched_rows, CURATED_METADATA_COLUMNS)
    grouped: dict[str, list[dict]] = {}
    for row in enriched_rows:
        grouped.setdefault(row["document_key"], []).append(row)

    unique_rows: list[dict] = []
    workstream_rows: list[dict] = []
    for document_key, group in grouped.items():
        representative = max(group, key=_representative_sort_key)
        workstreams = sorted({str(item.get("workstream") or "").strip() for item in group if str(item.get("workstream") or "").strip()})
        unique_row = {
            **representative,
            "workstreams": ";".join(workstreams),
            "raw_occurrence_count": len(group),
            "workstream_count": len(workstreams),
        }
        unique_rows.append(unique_row)

        per_workstream: dict[str, list[dict]] = {}
        for item in group:
            workstream = str(item.get("workstream") or "").strip()
            if not workstream:
                continue
            per_workstream.setdefault(workstream, []).append(item)

        for workstream, ws_rows in per_workstream.items():
            workstream_rows.append(
                {
                    "document_key": document_key,
                    "document_id": representative.get("document_id", ""),
                    "workstream": workstream,
                    "title": representative.get("title", ""),
                    "canonical_url": representative.get("canonical_url", ""),
                    "score_max": max(_as_float(item.get("score")) for item in ws_rows),
                    "raw_occurrence_count": len(ws_rows),
                }
            )

    unique_df = _frame(unique_rows, UNIQUE_DOCUMENT_COLUMNS).sort_values(
        by=["score", "raw_occurrence_count", "title"],
        ascending=[False, False, True],
        na_position="last",
    )
    workstream_df = _frame(workstream_rows, WORKSTREAM_MAP_COLUMNS).sort_values(
        by=["workstream", "score_max", "title"],
        ascending=[True, False, True],
        na_position="last",
    )
    return metadata_df, unique_df, workstream_df


def _build_qa_report(metadata_df: pd.DataFrame, unique_df: pd.DataFrame, workstream_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    summary_rows = [
        {"metric": "raw_records", "value": int(len(metadata_df))},
        {"metric": "unique_documents", "value": int(len(unique_df))},
        {"metric": "duplicates_removed", "value": int(max(len(metadata_df) - len(unique_df), 0))},
        {"metric": "document_workstream_links", "value": int(len(workstream_df))},
        {
            "metric": "documents_with_pdf_or_html",
            "value": int(unique_df["is_full_text_available"].fillna(False).astype(bool).sum()) if not unique_df.empty else 0,
        },
        {
            "metric": "documents_metadata_only",
            "value": int(unique_df["is_metadata_only"].fillna(False).astype(bool).sum()) if not unique_df.empty else 0,
        },
        {
            "metric": "documents_prioritized",
            "value": int(
                (
                    unique_df["domains"].fillna("").astype(str).str.len().gt(0)
                    & unique_df["score"].fillna(0).astype(float).ge(8)
                ).sum()
            ) if not unique_df.empty else 0,
        },
        {"metric": "ocr_attempted", "value": int(unique_df["ocr_attempted"].fillna(False).astype(bool).sum()) if not unique_df.empty else 0},
        {"metric": "ocr_docs", "value": int(unique_df["used_ocr"].fillna(False).astype(bool).sum()) if not unique_df.empty else 0},
        {
            "metric": "ocr_failed",
            "value": int((unique_df["ocr_attempted"].fillna(False).astype(bool) & ~unique_df["used_ocr"].fillna(False).astype(bool)).sum()) if not unique_df.empty else 0,
        },
        {
            "metric": "ocr_unavailable",
            "value": int(unique_df["extraction_status"].fillna("").eq("ocr_unavailable").sum()) if not unique_df.empty else 0,
        },
        {
            "metric": "ok_native_low_confidence",
            "value": int(unique_df["extraction_status"].fillna("").eq("ok_native_low_confidence").sum()) if not unique_df.empty else 0,
        },
        {"metric": "missing_title", "value": int(unique_df["title"].fillna("").eq("").sum()) if not unique_df.empty else 0},
        {"metric": "missing_year", "value": int(unique_df["year"].fillna("").astype(str).eq("").sum()) if not unique_df.empty else 0},
        {
            "metric": "missing_canonical_url_without_identifier",
            "value": int(
                (
                    unique_df["canonical_url"].fillna("").eq("")
                    & unique_df["doi"].fillna("").eq("")
                    & unique_df["pmid"].fillna("").eq("")
                    & unique_df["pmcid"].fillna("").eq("")
                ).sum()
            ) if not unique_df.empty else 0,
        },
    ]

    duplicate_details = pd.DataFrame(columns=["document_key", "title", "raw_occurrence_count", "workstream_count", "canonical_url"])
    if not unique_df.empty:
        duplicate_details = unique_df.loc[
            unique_df["raw_occurrence_count"].fillna(0).astype(int).gt(1),
            ["document_key", "title", "raw_occurrence_count", "workstream_count", "canonical_url"],
        ].sort_values(by=["raw_occurrence_count", "title"], ascending=[False, True])

    extraction_summary = pd.DataFrame(columns=["extraction_status", "n_documents"])
    if not unique_df.empty:
        extraction_summary = (
            unique_df.groupby("extraction_status", dropna=False)
            .size()
            .reset_index(name="n_documents")
            .sort_values(by=["n_documents", "extraction_status"], ascending=[False, True])
        )

    workstream_summary = pd.DataFrame(columns=["workstream", "unique_documents", "raw_occurrences", "prioritized_documents"])
    if not workstream_df.empty:
        joined = workstream_df.merge(
            unique_df[["document_key", "domains", "score"]],
            on="document_key",
            how="left",
        )
        joined["is_prioritized"] = joined["domains"].fillna("").astype(str).str.len().gt(0) & joined["score"].fillna(0).astype(float).ge(8)
        workstream_summary = (
            joined.groupby("workstream", dropna=False)
            .agg(
                unique_documents=("document_key", "nunique"),
                raw_occurrences=("raw_occurrence_count", "sum"),
                prioritized_documents=("is_prioritized", "sum"),
            )
            .reset_index()
            .sort_values(by=["unique_documents", "workstream"], ascending=[False, True])
        )

    missing_fields = pd.DataFrame(columns=["document_key", "title", "doi", "pmid", "pmcid", "canonical_url", "year", "workstreams"])
    if not unique_df.empty:
        missing_fields = unique_df.loc[
            unique_df["title"].fillna("").eq("")
            | unique_df["year"].fillna("").astype(str).eq("")
            | (
                unique_df["canonical_url"].fillna("").eq("")
                & unique_df["doi"].fillna("").eq("")
                & unique_df["pmid"].fillna("").eq("")
                & unique_df["pmcid"].fillna("").eq("")
            ),
            ["document_key", "title", "doi", "pmid", "pmcid", "canonical_url", "year", "workstreams"],
        ].sort_values(by=["title", "document_key"], ascending=[True, True])

    return {
        "summary": pd.DataFrame(summary_rows),
        "extraction_status": extraction_summary,
        "duplicate_groups": duplicate_details,
        "by_workstream": workstream_summary,
        "missing_fields": missing_fields,
    }


def _write_table_pair(df: pd.DataFrame, csv_path: Path, xlsx_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    xlsx_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df.to_excel(xlsx_path, index=False)


def write_curated_outputs(
    all_rows: list[dict],
    download_manifest: list[dict],
    extraction_manifest: list[dict],
    out_dir: Path,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)

    enriched_rows = _enrich_rows(all_rows, extraction_manifest)
    metadata_df, unique_df, workstream_df = _build_unique_documents(enriched_rows)
    qa_sheets = _build_qa_report(metadata_df, unique_df, workstream_df)
    prisma_flow = build_prisma_flow(enriched_rows, download_manifest, extraction_manifest)

    _write_table_pair(
        metadata_df,
        out_dir / "NUTEV_METADATA_CURATED.csv",
        out_dir / "NUTEV_METADATA_CURATED.xlsx",
    )
    _write_table_pair(
        unique_df,
        out_dir / "NUTEV_DOCUMENTS_UNIQUE.csv",
        out_dir / "NUTEV_DOCUMENTS_UNIQUE.xlsx",
    )
    workstream_df.to_csv(
        out_dir / "NUTEV_DOCUMENT_WORKSTREAM_MAP.csv",
        index=False,
        encoding="utf-8-sig",
    )

    with pd.ExcelWriter(out_dir / "NUTEV_QA_REPORT.xlsx") as writer:
        for sheet_name, sheet_df in qa_sheets.items():
            write_excel_sheet(writer, sheet_df, sheet_name)

    prisma_df = pd.DataFrame([prisma_flow])
    with pd.ExcelWriter(out_dir / "NUTEV_PRISMA_FLOW_CORRIGIDO.xlsx") as writer:
        write_excel_sheet(writer, prisma_df, "summary")
        write_excel_sheet(writer, qa_sheets["summary"], "qa_summary")

    return {
        "metadata": metadata_df,
        "unique_documents": unique_df,
        "workstream_map": workstream_df,
        "qa_sheets": qa_sheets,
        "prisma_flow": prisma_flow,
    }
