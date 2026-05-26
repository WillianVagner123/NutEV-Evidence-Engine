from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

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
    "guideline",
    "guidelines",
    "clinical practice guideline",
    "practice advisory",
    "practice guidance",
    "guidance statement",
    "guideline update",
    "clinical practice update",
    "best practice advice",
    "living guideline",
    "consensus",
    "consensus statement",
    "consensus report",
    "consensus guidance",
    "scientific statement",
    "scientific advisory",
    "position statement",
    "position paper",
    "joint statement",
    "joint guideline",
    "clinical guidance",
    "clinical decision pathway",
    "decision pathway",
    "clinical practice recommendation",
    "clinical practice recommendations",
    "standards of care",
    "standards of medical care",
    "standards of medical care in diabetes",
    "systematic review",
    "meta-analysis",
    "meta analysis",
    "network meta-analysis",
    "network meta analysis",
    "umbrella review",
    "lifestyle medicine",
    "culinary medicine",
    "food literacy",
    "food and nutrition literacy",
    "nutrition literacy",
    "food agency",
    "food is medicine",
    "food as medicine",
    "produce prescription",
    "produce prescriptions",
    "produce prescription program",
    "produce rx",
    "fruit and vegetable prescription",
    "healthy food prescription",
    "food prescription program",
    "medically tailored meal",
    "medically tailored meals",
    "medically tailored grocery",
    "medically tailored groceries",
    "teaching kitchen",
    "teaching kitchens",
    "nutrition security",
    "food environment",
    "retail food environment",
    "healthy food access",
    "healthy food procurement",
    "front-of-pack labeling",
    "front-of-pack labelling",
    "menu labeling",
    "menu labelling",
    "adherence",
    "implementation",
    "implementation trial",
    "implementation evaluation",
    "implementation science",
    "implementation strategy",
    "implementation strategies",
    "implementation framework",
    "implementation frameworks",
    "implementation outcomes",
    "implementation fidelity",
    "implementation determinant",
    "implementation determinants",
    "implementation barrier",
    "implementation barriers",
    "implementation facilitator",
    "implementation facilitators",
    "implementation climate",
    "organizational readiness",
    "readiness for implementation",
    "acceptability",
    "feasibility",
    "penetration",
    "sustainment",
    "hybrid effectiveness-implementation",
    "hybrid effectiveness implementation",
    "hybrid type 1",
    "hybrid type 2",
    "hybrid type 3",
    "cfir",
    "re-aim",
    "normalization process theory",
    "theoretical domains framework",
    "motivational interviewing",
    "behavior change technique",
    "behavior change wheel",
    "behaviour change wheel",
    "com-b",
    "capability opportunity motivation behavior",
    "capability opportunity motivation behaviour",
    "intervention mapping",
    "implementation mapping",
    "process evaluation",
    "quality improvement",
    "quality improvement study",
    "real-world implementation",
    "real world implementation",
    "real-world evidence",
    "real world evidence",
    "knowledge translation",
    "practice facilitation",
    "audit and feedback",
    "care delivery",
    "service delivery",
    "health coaching",
    "telehealth",
    "telemedicine",
    "digital health",
    "mobile health",
    "mhealth",
    "ehealth",
    "virtual care",
    "remote coaching",
    "remote monitoring",
    "digital therapeutics",
    "self-management support",
    "scale-up",
    "scale up",
    "program implementation",
    "barrier",
    "facilitator",
    "commensality",
    "meal planning",
    "behavior change",
    "self-efficacy",
]

_PRIORITY_TEXT_FIELDS = (
    "title",
    "abstract",
    "snippet",
    "summary",
    "evidence_type",
    "domains",
    "outcomes",
    "diet_patterns",
    "clinical_conditions",
    "main_terms",
    "journal",
    "source_institution",
)

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
        return text.strip().rstrip("/").lower().removeprefix("www.")

    netloc = parsed.netloc.lower().removeprefix("www.")
    if parsed.scheme.lower() == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    if parsed.scheme.lower() == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]

    path = parsed.path.rstrip("/") or "/"
    # Ignore scheme, fragments, and tracking parameters for operational dedup.
    return f"{netloc}{path}".rstrip("/")


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
    text = " ".join(_as_text(row.get(field)) for field in _PRIORITY_TEXT_FIELDS).lower()
    editorial_tier = _as_text(row.get("editorial_priority_tier")).lower()
    high_value_editorial = editorial_tier in _A1_PROXY_TIERS
    matches_priority_scope = any(term in text for term in _PRIORITY_TERMS)
    return (score >= 8 and matches_priority_scope) or (score >= 7 and high_value_editorial)


def _curate_row(row: dict) -> dict:
    curated = {
        column: _as_text(row.get(column)) for column in REQUIRED_METADATA_COLUMNS
    }
    curated["document_id"] = _as_text(row.get("document_id") or row.get("id"))
    curated["title"] = _as_text(row.get("title"))
    curated["doi"] = _as_text(row.get("doi"))
    curated["pmid"] = _as_text(row.get("pmid"))
    curated["pmcid"] = _as_text(row.get("pmcid"))
    curated["abstract"] = _as_text(row.get("abstract") or row.get("summary"))
    curated["snippet"] = _as_text(row.get("snippet"))
    curated["summary"] = _as_text(row.get("summary"))
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
    curated["journal"] = _as_text(row.get("journal"))
    curated["source_institution"] = _as_text(row.get("source_institution"))
    curated["editorial_priority_score"] = row.get("editorial_priority_score") or ""
    curated["editorial_priority_tier"] = _as_text(
        row.get("editorial_priority_tier")
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

def _ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for column in columns:
        if column not in out.columns:
            out[column] = ""
    return out[columns]


def _build_unique_documents(curated_rows: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for row in curated_rows:
        key = _as_text(row.get("document_key")) or _hash_fallback(row)
        groups.setdefault(key, []).append(row)

    unique_rows: list[dict] = []
    for key, rows in groups.items():
        best = sorted(rows, key=_rank_row, reverse=True)[0]
        item = {column: best.get(column, "") for column in UNIQUE_DOCUMENT_COLUMNS}
        item["document_key"] = key
        item["document_key_type"] = best.get("document_key_type", "")
        item["workstreams"] = "; ".join(
            sorted({ _as_text(row.get("workstream")) for row in rows if _as_text(row.get("workstream")) })
        )
        item["document_ids"] = "; ".join(
            sorted({ _as_text(row.get("document_id")) for row in rows if _as_text(row.get("document_id")) })
        )
        item["source_occurrences"] = len(rows)
        item["has_full_text"] = any(bool(row.get("has_full_text")) for row in rows)
        item["is_metadata_only"] = not item["has_full_text"]
        item["is_prioritized"] = any(bool(row.get("is_prioritized")) for row in rows)
        unique_rows.append(item)

    return sorted(unique_rows, key=_rank_row, reverse=True)


def curate_outputs(rows: list[dict], output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    curated_rows = [_curate_row(row) for row in rows]
    curated_df = pd.DataFrame(curated_rows)
    if curated_df.empty:
        curated_df = pd.DataFrame(columns=CURATED_METADATA_COLUMNS)
    else:
        curated_df = _ensure_columns(curated_df, CURATED_METADATA_COLUMNS)

    curated_df = sanitize_dataframe_for_excel(curated_df)
    curated_df.to_csv(output_dir / "curated_metadata.csv", index=False, encoding="utf-8-sig")
    write_excel_file(curated_df, output_dir / "curated_metadata.xlsx")

    unique_rows = _build_unique_documents(curated_rows)
    unique_df = pd.DataFrame(unique_rows)
    if unique_df.empty:
        unique_df = pd.DataFrame(columns=UNIQUE_DOCUMENT_COLUMNS)
    else:
        unique_df = _ensure_columns(unique_df, UNIQUE_DOCUMENT_COLUMNS)

    unique_df = sanitize_dataframe_for_excel(unique_df)
    unique_df.to_csv(output_dir / "unique_documents.csv", index=False, encoding="utf-8-sig")
    write_excel_file(unique_df, output_dir / "unique_documents.xlsx")

    top_df = unique_df.head(100).copy()
    if not top_df.empty:
        top_df = _ensure_columns(top_df, TOP_A1_OPERATIONAL_COLUMNS)
    else:
        top_df = pd.DataFrame(columns=TOP_A1_OPERATIONAL_COLUMNS)
    write_excel_file(top_df, output_dir / "top_operational_documents.xlsx")

    workstream_rows = []
    for row in curated_rows:
        workstream_rows.append({
            "document_key": row.get("document_key", ""),
            "document_id": row.get("document_id", ""),
            "workstream": row.get("workstream", ""),
            "source_provider": row.get("source_provider", ""),
            "title": row.get("title", ""),
            "year": row.get("year", ""),
            "download_status": row.get("download_status", ""),
            "extraction_status": row.get("extraction_status", ""),
            "is_prioritized": row.get("is_prioritized", False),
        })

    workstream_df = pd.DataFrame(workstream_rows)
    if workstream_df.empty:
        workstream_df = pd.DataFrame(columns=WORKSTREAM_MAP_COLUMNS)
    else:
        workstream_df = _ensure_columns(workstream_df, WORKSTREAM_MAP_COLUMNS)
    workstream_df.to_csv(output_dir / "workstream_document_map.csv", index=False, encoding="utf-8-sig")

    summary = {
        "input_rows": len(rows),
        "curated_rows": len(curated_rows),
        "unique_documents": len(unique_rows),
        "metadata_only_documents": int(unique_df["is_metadata_only"].astype(bool).sum()) if not unique_df.empty else 0,
        "prioritized_documents": int(unique_df["is_prioritized"].astype(bool).sum()) if not unique_df.empty else 0,
    }

    (output_dir / "curation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary
