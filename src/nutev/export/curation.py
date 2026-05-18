from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pandas as pd

from nutev.export.excel_writer import (
    sanitize_dataframe_for_excel,
    write_excel_file,
    write_excel_sheet,
)
from nutev.export.metadata_tables import REQUIRED_METADATA_COLUMNS

CURATED_METADATA_COLUMNS = REQUIRED_METADATA_COLUMNS + [
    "document_key",
    "document_key_type",
    "doi_normalized",
    "url_normalized",
    "title_normalized",
    "year_normalized",
    "workstream_list",
    "has_full_text",
    "is_metadata_only",
    "is_prioritized",
]

UNIQUE_DOCUMENT_COLUMNS = [
    "document_key",
    "document_key_type",
    "title",
    "year",
    "doi",
    "pmid",
    "pmcid",
    "original_url",
    "final_url",
    "source_provider",
    "source_institution",
    "journal",
    "evidence_type",
    "download_status",
    "capture_status",
    "extraction_status",
    "relevance_score",
    "editorial_priority_score",
    "editorial_priority_tier",
    "workstreams",
    "document_ids",
    "source_occurrences",
    "has_full_text",
    "is_metadata_only",
    "is_prioritized",
]

TOP_A1_OPERATIONAL_COLUMNS = [
    "document_key",
    "title",
    "journal",
    "source_institution",
    "workstreams",
    "year",
    "evidence_type",
    "relevance_score",
    "editorial_priority_score",
    "editorial_priority_tier",
    "download_status",
    "capture_status",
    "extraction_status",
    "has_full_text",
    "is_metadata_only",
    "is_prioritized",
    "doi",
    "pmid",
    "pmcid",
    "final_url",
    "original_url",
]

WORKSTREAM_MAP_COLUMNS = [
    "document_key",
    "document_id",
    "workstream",
    "source_provider",
    "title",
    "year",
    "download_status",
    "extraction_status",
    "is_prioritized",
]

PRISMA_COLUMNS = [
    "registros_identificados",
    "duplicados_removidos",
    "registros_triados",
    "documentos_com_pdf_ou_html",
    "documentos_metadata_only",
    "documentos_priorizados",
]

PRISMA_NOTE_COLUMNS = ["nota"]
QA_SUMMARY_COLUMNS = ["metric", "value"]
DUPLICATE_SUMMARY_COLUMNS = [
    "document_key_type",
    "duplicate_documents",
    "duplicate_rows",
]
MISSING_BY_WORKSTREAM_COLUMNS = [
    "workstream",
    "missing_title",
    "missing_url",
    "missing_year",
    "missing_evidence_type",
]

_PRIORITY_TERMS = [
    "obesity",
    "obesidade",
    "overweight",
    "cardiometabolic",
    "diabetes",
    "hypertension",
    "dyslipidemia",
    "masld",
    "nafld",
    "mediterranean",
    "dash",
    "mind",
    "plant-based",
    "eat-lancet",
    "dietary guideline",
    "food-based dietary guideline",
    "lifestyle medicine",
    "culinary medicine",
    "food literacy",
    "adherence",
    "implementation",
    "barrier",
    "facilitator",
    "commensality",
    "meal planning",
    "behavior change",
    "self-efficacy",
]

_A1_PROXY_TIERS = {"a1_proxy_high", "a1_proxy_moderate"}

_WHITESPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def _as_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple, set)):
        return "; ".join(_as_text(v) for v in value if _as_text(v))
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def _normalize_doi(value: object) -> str:
    text = _as_text(value).lower()
    if not text:
        return ""
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    return text.strip().strip("/")


def _normalize_url(value: object) -> str:
    text = _as_text(value)
    if not text:
        return ""
    parsed = urlsplit(text)
    if not parsed.scheme or not parsed.netloc:
        return text.strip().rstrip("/").lower()
    path = parsed.path.rstrip("/") or "/"
    normalized = urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), path, "", "")
    )
    return normalized.rstrip("/")


def _normalize_title(value: object) -> str:
    text = _WHITESPACE_RE.sub(" ", _as_text(value).lower()).strip()
    return _NON_ALNUM_RE.sub(" ", text).strip()


def _normalize_year(value: object) -> str:
    text = _as_text(value)
    if not text:
        return ""
    try:
        year = int(float(text))
    except Exception:
        return ""
    return str(year)


def _hash_fallback(row: dict) -> str:
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True, default=str)
    # Deterministic operational fallback key, not a security primitive.
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]  # noqa: S324


def _compute_document_key(row: dict) -> tuple[str, str]:
    doi = _normalize_doi(row.get("doi"))
    if doi:
        return doi, "doi"

    pmid = _as_text(row.get("pmid"))
    if pmid:
        return pmid, "pmid"

    pmcid = _as_text(row.get("pmcid"))
    if pmcid:
        return pmcid, "pmcid"

    url = _normalize_url(
        row.get("final_url") or row.get("original_url") or row.get("url")
    )
    if url:
        return url, "url"

    title = _normalize_title(row.get("title"))
    year = _normalize_year(row.get("year"))
    if title and year:
        return f"{title}::{year}", "title_year"

    return _hash_fallback(row), "row_hash"


def _has_full_text(row: dict) -> bool:
    statuses = {
        _as_text(row.get("download_status")).lower(),
        _as_text(row.get("capture_status")).lower(),
        _as_text(row.get("extraction_status")).lower(),
    }
    if "pdf" in statuses or "html_snapshot" in statuses or "ok" in statuses:
        return True
    return bool(_as_text(row.get("file_path")) or _as_text(row.get("text_path")))


def _is_prioritized(row: dict) -> bool:
    try:
        score = float(row.get("relevance_score") or row.get("score") or 0)
    except Exception:
        score = 0.0
    text = " ".join(
        [
            _as_text(row.get("title")),
            _as_text(row.get("evidence_type")),
            _as_text(row.get("domains")),
            _as_text(row.get("outcomes")),
            _as_text(row.get("diet_patterns")),
            _as_text(row.get("clinical_conditions")),
            _as_text(row.get("main_terms")),
        ]
    ).lower()
    return score >= 8 and any(term in text for term in _PRIORITY_TERMS)


def _curate_row(row: dict) -> dict:
    curated = {
        column: _as_text(row.get(column)) for column in REQUIRED_METADATA_COLUMNS
    }
    curated["document_id"] = _as_text(row.get("document_id") or row.get("id"))
    curated["title"] = _as_text(row.get("title"))
    curated["doi"] = _as_text(row.get("doi"))
    curated["pmid"] = _as_text(row.get("pmid"))
    curated["pmcid"] = _as_text(row.get("pmcid"))
    curated["original_url"] = _as_text(row.get("original_url") or row.get("url"))
    curated["final_url"] = _as_text(
        row.get("final_url") or row.get("resolved_url") or row.get("url")
    )
    curated["artifact_paths"] = _as_text(
        row.get("artifact_paths") or row.get("file_path")
    )
    curated["source_provider"] = _as_text(
        row.get("source_provider") or row.get("source")
    )
    curated["workstream"] = _as_text(row.get("workstream"))
    curated["capture_status"] = _as_text(row.get("capture_status") or "missing")
    curated["download_status"] = _as_text(
        row.get("download_status") or ("pdf" if row.get("file_path") else "metadata_only")
    )
    curated["extraction_status"] = _as_text(
        row.get("extraction_status") or "missing"
    )
    curated["relevance_score"] = row.get("relevance_score") or row.get("score") or ""
    curated["novelty_score"] = row.get("novelty_score") or ""
    curated["domains"] = _as_text(row.get("domains"))
    curated["outcomes"] = _as_text(row.get("outcomes"))
    curated["diet_patterns"] = _as_text(
        row.get("diet_patterns") or row.get("diet_pattern")
    )
    curated["clinical_conditions"] = _as_text(
        row.get("clinical_conditions") or row.get("clinical_condition")
    )

    document_key, document_key_type = _compute_document_key(curated)
    curated["document_key"] = document_key
    curated["document_key_type"] = document_key_type
    curated["doi_normalized"] = _normalize_doi(curated.get("doi"))
    curated["url_normalized"] = _normalize_url(
        curated.get("final_url") or curated.get("original_url")
    )
    curated["title_normalized"] = _normalize_title(curated.get("title"))
    curated["year_normalized"] = _normalize_year(curated.get("year"))
    curated["workstream_list"] = curated.get("workstream", "")
    curated["has_full_text"] = _has_full_text(curated)
    curated["is_metadata_only"] = not curated["has_full_text"]
    curated["is_prioritized"] = _is_prioritized(curated)
    return curated


def _rank_row(row: dict) -> tuple[int, int, float, float, int, str]:
    try:
        score = float(row.get("relevance_score") or 0)
    except Exception:
        score = 0.0
    try:
        editorial_score = float(row.get("editorial_priority_score") or 0)
    except Exception:
        editorial_score = 0.0
    try:
        year = int(row.get("year_normalized") or 0)
    except Exception:
        year = 0
    return (
        int(bool(row.get("has_full_text"))),
        int(bool(row.get("is_prioritized"))),
        editorial_score,
        score,
        year,
        _as_text(row.get("title")),
    )


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def _build_unique_documents(curated_rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for row in curated_rows:
        grouped.setdefault(row["document_key"], []).append(row)

    unique_rows = []
    for document_key in sorted(grouped):
        group = sorted(grouped[document_key], key=_rank_row, reverse=True)
        best = dict(group[0])
        workstreams = sorted(
            {
                _as_text(item.get("workstream"))
                for item in group
                if _as_text(item.get("workstream"))
            }
        )
        document_ids = sorted(
            {
                _as_text(item.get("document_id"))
                for item in group
                if _as_text(item.get("document_id"))
            }
        )
        best.update(
            {
                "workstreams": "; ".join(workstreams),
                "document_ids": "; ".join(document_ids),
                "source_occurrences": len(group),
                "has_full_text": any(
                    bool(item.get("has_full_text")) for item in group
                ),
                "is_metadata_only": not any(
                    bool(item.get("has_full_text")) for item in group
                ),
                "is_prioritized": any(
                    bool(item.get("is_prioritized")) for item in group
                ),
            }
        )
        unique_rows.append(
            {column: best.get(column, "") for column in UNIQUE_DOCUMENT_COLUMNS}
        )
    return unique_rows


def _build_workstream_map(curated_rows: list[dict]) -> list[dict]:
    selected: dict[tuple[str, str], dict] = {}
    for row in sorted(curated_rows, key=_rank_row, reverse=True):
        workstream = _as_text(row.get("workstream")) or "unassigned"
        key = (row["document_key"], workstream)
        selected.setdefault(key, row)
    return [
        {
            column: row.get(
                column if column != "workstream" else "workstream", ""
            )
            for column in WORKSTREAM_MAP_COLUMNS
        }
        for _, row in sorted(selected.items())
    ]


def _build_top_a1_operational(unique_rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(unique_rows)
    if df.empty:
        return pd.DataFrame(columns=TOP_A1_OPERATIONAL_COLUMNS)

    editorial_score = pd.to_numeric(df.get("editorial_priority_score", 0), errors="coerce").fillna(0)
    relevance_score = pd.to_numeric(df.get("relevance_score", 0), errors="coerce").fillna(0)
    has_full_text = df.get("has_full_text", False).astype(bool)
    is_prioritized = df.get("is_prioritized", False).astype(bool)
    tier = df.get("editorial_priority_tier", "").fillna("")

    mask = (
        tier.isin(_A1_PROXY_TIERS)
        & is_prioritized
        & ((has_full_text & (relevance_score >= 10)) | (editorial_score >= 12))
    )
    top_df = df.loc[mask, TOP_A1_OPERATIONAL_COLUMNS].copy()
    if top_df.empty:
        return pd.DataFrame(columns=TOP_A1_OPERATIONAL_COLUMNS)

    top_df["_editorial_sort"] = pd.to_numeric(
        top_df["editorial_priority_score"], errors="coerce"
    ).fillna(0)
    top_df["_relevance_sort"] = pd.to_numeric(
        top_df["relevance_score"], errors="coerce"
    ).fillna(0)
    top_df["_full_text_sort"] = top_df["has_full_text"].astype(bool).astype(int)
    top_df = top_df.sort_values(
        ["_full_text_sort", "_editorial_sort", "_relevance_sort", "year", "title"],
        ascending=[False, False, False, False, True],
    ).drop(columns=["_editorial_sort", "_relevance_sort", "_full_text_sort"])
    return top_df


def _build_duplicate_rows(curated_rows: list[dict]) -> pd.DataFrame:
    counts: dict[str, int] = {}
    for row in curated_rows:
        counts[row["document_key"]] = counts.get(row["document_key"], 0) + 1
    duplicates = []
    for row in curated_rows:
        occurrences = counts[row["document_key"]]
        if occurrences > 1:
            duplicates.append(
                {
                    "document_key": row["document_key"],
                    "document_key_type": row["document_key_type"],
                    "document_id": row.get("document_id", ""),
                    "title": row.get("title", ""),
                    "workstream": row.get("workstream", ""),
                    "occurrences": occurrences,
                }
            )
    return pd.DataFrame(
        duplicates,
        columns=[
            "document_key",
            "document_key_type",
            "document_id",
            "title",
            "workstream",
            "occurrences",
        ],
    )


def _build_duplicate_summary(curated_rows: list[dict]) -> pd.DataFrame:
    grouped: dict[str, dict[str, int]] = {}
    key_counts: dict[str, int] = {}
    key_types: dict[str, str] = {}
    for row in curated_rows:
        key = row["document_key"]
        key_counts[key] = key_counts.get(key, 0) + 1
        key_types[key] = row["document_key_type"]
    for key, count in key_counts.items():
        if count <= 1:
            continue
        key_type = key_types[key]
        bucket = grouped.setdefault(
            key_type, {"duplicate_documents": 0, "duplicate_rows": 0}
        )
        bucket["duplicate_documents"] += 1
        bucket["duplicate_rows"] += count - 1
    rows = [
        {
            "document_key_type": key_type,
            "duplicate_documents": values["duplicate_documents"],
            "duplicate_rows": values["duplicate_rows"],
        }
        for key_type, values in sorted(grouped.items())
    ]
    return pd.DataFrame(rows, columns=DUPLICATE_SUMMARY_COLUMNS)


def _build_missing_canonical_rows(curated_rows: list[dict]) -> pd.DataFrame:
    rows = []
    for row in curated_rows:
        missing = []
        if not _as_text(row.get("title")):
            missing.append("title")
        if not _as_text(row.get("final_url") or row.get("original_url")):
            missing.append("url")
        if not _as_text(row.get("year")):
            missing.append("year")
        if not _as_text(row.get("evidence_type")):
            missing.append("evidence_type")
        if missing:
            rows.append(
                {
                    "document_key": row.get("document_key", ""),
                    "document_id": row.get("document_id", ""),
                    "title": row.get("title", ""),
                    "workstream": row.get("workstream", ""),
                    "missing_fields": "; ".join(missing),
                }
            )
    return pd.DataFrame(
        rows,
        columns=[
            "document_key",
            "document_id",
            "title",
            "workstream",
            "missing_fields",
        ],
    )


def _build_missing_by_workstream(curated_rows: list[dict]) -> pd.DataFrame:
    grouped: dict[str, dict[str, int]] = {}
    for row in curated_rows:
        workstream = _as_text(row.get("workstream")) or "unassigned"
        bucket = grouped.setdefault(
            workstream,
            {
                "missing_title": 0,
                "missing_url": 0,
                "missing_year": 0,
                "missing_evidence_type": 0,
            },
        )
        if not _as_text(row.get("title")):
            bucket["missing_title"] += 1
        if not _as_text(row.get("final_url") or row.get("original_url")):
            bucket["missing_url"] += 1
        if not _as_text(row.get("year")):
            bucket["missing_year"] += 1
        if not _as_text(row.get("evidence_type")):
            bucket["missing_evidence_type"] += 1
    rows = [
        {"workstream": workstream, **values}
        for workstream, values in sorted(grouped.items())
    ]
    return pd.DataFrame(rows, columns=MISSING_BY_WORKSTREAM_COLUMNS)


def _build_status_counts(curated_rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(curated_rows)
    if df.empty:
        return pd.DataFrame(columns=["download_status", "extraction_status", "n"])
    return (
        df.groupby(["download_status", "extraction_status"], dropna=False)
        .size()
        .reset_index(name="n")
        .sort_values(
            ["n", "download_status", "extraction_status"],
            ascending=[False, True, True],
        )
    )


def _build_workstream_counts(curated_rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(curated_rows)
    if df.empty:
        return pd.DataFrame(columns=["workstream", "n"])
    return df.groupby("workstream", dropna=False).size().reset_index(
        name="n"
    ).sort_values(["n", "workstream"], ascending=[False, True])


def _build_qa_summary(
    curated_rows: list[dict], unique_rows: list[dict], workstream_map: list[dict], top_a1_rows: pd.DataFrame
) -> pd.DataFrame:
    duplicate_rows = max(0, len(curated_rows) - len(unique_rows))
    summary = [
        {"metric": "raw_records", "value": len(curated_rows)},
        {"metric": "unique_documents", "value": len(unique_rows)},
        {"metric": "document_workstream_pairs", "value": len(workstream_map)},
        {"metric": "duplicate_rows_removed", "value": duplicate_rows},
        {
            "metric": "documents_with_full_text",
            "value": sum(1 for row in unique_rows if row.get("has_full_text")),
        },
        {
            "metric": "documents_metadata_only",
            "value": sum(1 for row in unique_rows if row.get("is_metadata_only")),
        },
        {
            "metric": "documents_prioritized",
            "value": sum(1 for row in unique_rows if row.get("is_prioritized")),
        },
        {
            "metric": "top_a1_operational_documents",
            "value": int(len(top_a1_rows.index)),
        },
        {
            "metric": "top_a1_operational_full_text",
            "value": int(top_a1_rows["has_full_text"].astype(bool).sum()) if not top_a1_rows.empty else 0,
        },
        {
            "metric": "missing_title",
            "value": sum(
                1 for row in curated_rows if not _as_text(row.get("title"))
            ),
        },
        {
            "metric": "missing_url",
            "value": sum(
                1
                for row in curated_rows
                if not _as_text(row.get("final_url") or row.get("original_url"))
            ),
        },
        {
            "metric": "missing_year",
            "value": sum(1 for row in curated_rows if not _as_text(row.get("year"))),
        },
        {
            "metric": "missing_evidence_type",
            "value": sum(
                1
                for row in curated_rows
                if not _as_text(row.get("evidence_type"))
            ),
        },
    ]
    return pd.DataFrame(summary, columns=QA_SUMMARY_COLUMNS)


def _build_prisma_corrected(
    curated_rows: list[dict], unique_rows: list[dict]
) -> pd.DataFrame:
    flow = {
        "registros_identificados": len(curated_rows),
        "duplicados_removidos": max(0, len(curated_rows) - len(unique_rows)),
        "registros_triados": len(unique_rows),
        "documentos_com_pdf_ou_html": sum(
            1 for row in unique_rows if row.get("has_full_text")
        ),
        "documentos_metadata_only": sum(
            1 for row in unique_rows if row.get("is_metadata_only")
        ),
        "documentos_priorizados": sum(
            1 for row in unique_rows if row.get("is_prioritized")
        ),
    }
    return pd.DataFrame([flow], columns=PRISMA_COLUMNS)


def curate_outputs(rows: list[dict], curated_dir: Path) -> dict[str, int]:
    curated_dir.mkdir(parents=True, exist_ok=True)

    curated_rows = [_curate_row(row) for row in rows]
    curated_df = pd.DataFrame(curated_rows, columns=CURATED_METADATA_COLUMNS)
    unique_rows = _build_unique_documents(curated_rows)
    unique_df = pd.DataFrame(unique_rows, columns=UNIQUE_DOCUMENT_COLUMNS)
    top_a1_df = _build_top_a1_operational(unique_rows)
    workstream_map = _build_workstream_map(curated_rows)
    workstream_df = pd.DataFrame(workstream_map, columns=WORKSTREAM_MAP_COLUMNS)
    duplicate_df = _build_duplicate_rows(curated_rows)
    duplicate_summary_df = _build_duplicate_summary(curated_rows)
    missing_df = _build_missing_canonical_rows(curated_rows)
    missing_by_workstream_df = _build_missing_by_workstream(curated_rows)
    status_df = _build_status_counts(curated_rows)
    workstream_counts_df = _build_workstream_counts(curated_rows)
    qa_summary_df = _build_qa_summary(curated_rows, unique_rows, workstream_map, top_a1_df)
    prisma_df = _build_prisma_corrected(curated_rows, unique_rows)
    prisma_notes_df = pd.DataFrame(
        [
            {
                "nota": (
                    "PRISMA operacional corrigido: registros_identificados = "
                    "linhas brutas; duplicados_removidos = linhas brutas - "
                    "documentos únicos; registros_triados = documentos únicos."
                )
            }
        ],
        columns=PRISMA_NOTE_COLUMNS,
    )

    _write_csv(curated_df, curated_dir / "NUTEV_METADATA_CURATED.csv")
    write_excel_file(
        sanitize_dataframe_for_excel(curated_df),
        curated_dir / "NUTEV_METADATA_CURATED.xlsx",
    )

    _write_csv(unique_df, curated_dir / "NUTEV_DOCUMENTS_UNIQUE.csv")
    write_excel_file(
        sanitize_dataframe_for_excel(unique_df),
        curated_dir / "NUTEV_DOCUMENTS_UNIQUE.xlsx",
    )

    _write_csv(top_a1_df, curated_dir / "NUTEV_TOP_A1_OPERACIONAL.csv")
    write_excel_file(
        sanitize_dataframe_for_excel(top_a1_df),
        curated_dir / "NUTEV_TOP_A1_OPERACIONAL.xlsx",
    )

    _write_csv(workstream_df, curated_dir / "NUTEV_DOCUMENT_WORKSTREAM_MAP.csv")

    with pd.ExcelWriter(curated_dir / "NUTEV_QA_REPORT.xlsx") as writer:
        write_excel_sheet(writer, qa_summary_df, "summary")
        write_excel_sheet(writer, top_a1_df, "top_a1_operacional")
        write_excel_sheet(writer, duplicate_df, "duplicate_keys")
        write_excel_sheet(writer, duplicate_summary_df, "duplicate_summary")
        write_excel_sheet(writer, missing_df, "missing_canonical")
        write_excel_sheet(writer, missing_by_workstream_df, "missing_by_workstream")
        write_excel_sheet(writer, status_df, "status_counts")
        write_excel_sheet(writer, workstream_counts_df, "workstream_counts")

    with pd.ExcelWriter(curated_dir / "NUTEV_PRISMA_FLOW_CORRIGIDO.xlsx") as writer:
        write_excel_sheet(writer, prisma_df, "flow")
        write_excel_sheet(writer, prisma_notes_df, "notes")

    return {
        "raw_records": len(curated_rows),
        "unique_documents": len(unique_rows),
        "document_workstream_pairs": len(workstream_map),
        "top_a1_operational_documents": int(len(top_a1_df.index)),
    }
