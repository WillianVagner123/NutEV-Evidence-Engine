from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd

from nutev.export.excel_writer import write_excel_file, write_excel_sheet
from nutev.export.metadata_tables import REQUIRED_METADATA_COLUMNS

CURATED_COLUMNS = REQUIRED_METADATA_COLUMNS + [
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
UNIQUE_COLUMNS = [
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
MAP_COLUMNS = ["document_key", "document_id", "workstream", "source_provider", "title", "year", "download_status", "extraction_status", "is_prioritized"]
PRISMA_COLUMNS = ["registros_identificados", "duplicados_removidos", "registros_triados", "documentos_com_pdf_ou_html", "documentos_metadata_only", "documentos_priorizados"]

_PRIORITY_TERMS = [
    "obesity", "obesidade", "overweight", "cardiometabolic", "diabetes", "hypertension", "dyslipidemia",
    "mediterranean", "dash", "plant-based", "dietary guideline", "guideline", "clinical practice guideline",
    "consensus", "scientific statement", "position statement", "standards of care", "systematic review",
    "meta-analysis", "umbrella review", "lifestyle medicine", "culinary medicine", "food literacy",
    "nutrition literacy", "teaching kitchen", "nutrition security", "food environment", "adherence",
    "implementation", "implementation science", "acceptability", "feasibility", "behavior change",
    "com-b", "health coaching", "digital health", "commensality", "meal planning", "self-efficacy",
]
_PRIORITY_FIELDS = ["title", "abstract", "snippet", "summary", "evidence_type", "domains", "outcomes", "diet_patterns", "clinical_conditions", "journal", "source_institution"]
_A1_TIERS = {"a1_proxy_high", "a1_proxy_moderate"}
_WS_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple, set)):
        return "; ".join(_text(v) for v in value if _text(v))
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def _norm_doi(value: object) -> str:
    text = _text(value).lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    return text.strip().strip("/")


def _norm_url(value: object) -> str:
    text = _text(value)
    if not text:
        return ""
    parsed = urlsplit(text)
    if not parsed.scheme or not parsed.netloc:
        return text.rstrip("/").lower().removeprefix("www.")
    netloc = parsed.netloc.lower().removeprefix("www.")
    if parsed.scheme.lower() == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    if parsed.scheme.lower() == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]
    return f"{netloc}{parsed.path.rstrip('/') or '/'}".rstrip("/")


def _norm_title(value: object) -> str:
    return _NON_ALNUM_RE.sub(" ", _WS_RE.sub(" ", _text(value).lower()).strip()).strip()


def _norm_year(value: object) -> str:
    try:
        return str(int(float(_text(value))))
    except Exception:
        return ""


def _document_key(row: dict) -> tuple[str, str]:
    doi = _norm_doi(row.get("doi"))
    if doi:
        return doi, "doi"
    for field, kind in (("pmid", "pmid"), ("pmcid", "pmcid")):
        value = _text(row.get(field)).lower()
        if value:
            return value, kind
    url = _norm_url(row.get("final_url") or row.get("resolved_url") or row.get("original_url") or row.get("url"))
    if url:
        return url, "url"
    title = _norm_title(row.get("title"))
    year = _norm_year(row.get("year"))
    if title and year:
        return f"{title}::{year}", "title_year"
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16], "row_hash"  # noqa: S324


def _has_full_text(row: dict) -> bool:
    statuses = {_text(row.get(name)).lower() for name in ("download_status", "capture_status", "extraction_status")}
    return bool({"pdf", "html_snapshot", "ok", "success"} & statuses) or bool(_text(row.get("artifact_paths") or row.get("file_path") or row.get("text_path")))


def _prioritized(row: dict) -> bool:
    try:
        score = float(row.get("relevance_score") or row.get("score") or 0)
    except Exception:
        score = 0.0
    haystack = " ".join(_text(row.get(field)) for field in _PRIORITY_FIELDS).lower()
    tier = _text(row.get("editorial_priority_tier")).lower()
    return (score >= 8 and any(term in haystack for term in _PRIORITY_TERMS)) or (score >= 7 and tier in _A1_TIERS)


def _curate_row(row: dict) -> dict:
    out = {column: _text(row.get(column)) for column in REQUIRED_METADATA_COLUMNS}
    out.update(
        {
            "document_id": _text(row.get("document_id") or row.get("id")),
            "title": _text(row.get("title")),
            "doi": _text(row.get("doi")),
            "pmid": _text(row.get("pmid")),
            "pmcid": _text(row.get("pmcid")),
            "abstract": _text(row.get("abstract") or row.get("summary")),
            "original_url": _text(row.get("original_url") or row.get("url")),
            "final_url": _text(row.get("final_url") or row.get("resolved_url") or row.get("url")),
            "artifact_paths": _text(row.get("artifact_paths") or row.get("file_path")),
            "source_provider": _text(row.get("source_provider") or row.get("source")),
            "workstream": _text(row.get("workstream")),
            "capture_status": _text(row.get("capture_status") or "missing"),
            "download_status": _text(row.get("download_status") or ("pdf" if row.get("file_path") else "metadata_only")),
            "extraction_status": _text(row.get("extraction_status") or "missing"),
            "relevance_score": row.get("relevance_score") or row.get("score") or "",
            "editorial_priority_score": row.get("editorial_priority_score") or "",
            "editorial_priority_tier": _text(row.get("editorial_priority_tier")),
            "domains": _text(row.get("domains")),
            "outcomes": _text(row.get("outcomes")),
            "diet_patterns": _text(row.get("diet_patterns") or row.get("diet_pattern")),
            "clinical_conditions": _text(row.get("clinical_conditions") or row.get("clinical_condition")),
            "journal": _text(row.get("journal")),
            "source_institution": _text(row.get("source_institution")),
        }
    )
    key, key_type = _document_key(out)
    out["document_key"] = key
    out["document_key_type"] = key_type
    out["doi_normalized"] = _norm_doi(out.get("doi"))
    out["url_normalized"] = _norm_url(out.get("final_url") or out.get("original_url"))
    out["title_normalized"] = _norm_title(out.get("title"))
    out["year_normalized"] = _norm_year(out.get("year"))
    out["workstream_list"] = out.get("workstream", "")
    out["has_full_text"] = _has_full_text(out)
    out["is_metadata_only"] = not out["has_full_text"]
    out["is_prioritized"] = _prioritized(out)
    return out


def _rank(row: dict) -> tuple[int, int, float, float, int, str]:
    def as_float(value: object) -> float:
        try:
            return float(value or 0)
        except Exception:
            return 0.0
    return (int(bool(row.get("has_full_text"))), int(bool(row.get("is_prioritized"))), as_float(row.get("editorial_priority_score")), as_float(row.get("relevance_score")), int(_norm_year(row.get("year")) or 0), _text(row.get("title")))


def _write_csv(rows: list[dict], path: Path, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def _unique_rows(rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["document_key"], []).append(row)
    out: list[dict] = []
    for key, group in grouped.items():
        best = dict(sorted(group, key=_rank, reverse=True)[0])
        best["document_key"] = key
        best["workstreams"] = "; ".join(sorted({r.get("workstream", "") for r in group if r.get("workstream")}))
        best["document_ids"] = "; ".join(sorted({r.get("document_id", "") for r in group if r.get("document_id")}))
        best["source_occurrences"] = len(group)
        best["has_full_text"] = any(bool(r.get("has_full_text")) for r in group)
        best["is_metadata_only"] = not best["has_full_text"]
        best["is_prioritized"] = any(bool(r.get("is_prioritized")) for r in group)
        out.append({column: best.get(column, "") for column in UNIQUE_COLUMNS})
    return sorted(out, key=_rank, reverse=True)


def _duplicate_summary(rows: list[dict]) -> list[dict]:
    if not rows:
        return []
    df = pd.DataFrame(rows)
    out = []
    for key_type, group in df.groupby("document_key_type", dropna=False):
        sizes = group.groupby("document_key").size()
        dup = sizes[sizes > 1]
        out.append({"document_key_type": key_type or "missing", "duplicate_documents": int(len(dup)), "duplicate_rows": int(dup.sum()) if len(dup) else 0})
    return sorted(out, key=lambda row: (row["duplicate_documents"], row["duplicate_rows"]), reverse=True)


def _missing_by_workstream(rows: list[dict]) -> list[dict]:
    if not rows:
        return []
    df = pd.DataFrame(rows)
    out = []
    for ws, group in df.groupby("workstream", dropna=False):
        out.append({
            "workstream": ws or "missing",
            "missing_title": int((group["title"].fillna("").astype(str).str.strip() == "").sum()),
            "missing_url": int(((group["final_url"].fillna("").astype(str).str.strip() == "") & (group["original_url"].fillna("").astype(str).str.strip() == "")).sum()),
            "missing_year": int((group["year"].fillna("").astype(str).str.strip() == "").sum()),
            "missing_evidence_type": int((group["evidence_type"].fillna("").astype(str).str.strip() == "").sum()),
        })
    return out


def curate_outputs(rows: list[dict], output_dir: Path) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    curated = [_curate_row(row) for row in rows]
    unique = _unique_rows(curated)
    mapped = [{column: row.get(column, "") for column in MAP_COLUMNS} for row in curated]
    prisma = [{
        "registros_identificados": len(curated),
        "duplicados_removidos": max(len(curated) - len(unique), 0),
        "registros_triados": len(unique),
        "documentos_com_pdf_ou_html": sum(1 for row in unique if bool(row.get("has_full_text"))),
        "documentos_metadata_only": sum(1 for row in unique if bool(row.get("is_metadata_only"))),
        "documentos_priorizados": sum(1 for row in unique if bool(row.get("is_prioritized"))),
    }]
    qa = [
        {"metric": "raw_records", "value": len(curated)},
        {"metric": "unique_documents", "value": len(unique)},
        {"metric": "duplicates_removed", "value": max(len(curated) - len(unique), 0)},
    ]
    _write_csv(curated, output_dir / "NUTEV_METADATA_CURATED.csv", CURATED_COLUMNS)
    _write_csv(unique, output_dir / "NUTEV_DOCUMENTS_UNIQUE.csv", UNIQUE_COLUMNS)
    _write_csv(mapped, output_dir / "NUTEV_DOCUMENT_WORKSTREAM_MAP.csv", MAP_COLUMNS)
    write_excel_file(pd.DataFrame(curated, columns=CURATED_COLUMNS), output_dir / "NUTEV_METADATA_CURATED.xlsx")
    write_excel_file(pd.DataFrame(unique, columns=UNIQUE_COLUMNS), output_dir / "NUTEV_DOCUMENTS_UNIQUE.xlsx")
    write_excel_file(pd.DataFrame(mapped, columns=MAP_COLUMNS), output_dir / "NUTEV_DOCUMENT_WORKSTREAM_MAP.xlsx")
    with pd.ExcelWriter(output_dir / "NUTEV_QA_REPORT.xlsx") as writer:
        write_excel_sheet(writer, pd.DataFrame(qa), "summary")
        write_excel_sheet(writer, pd.DataFrame(_duplicate_summary(curated)), "duplicate_summary")
        write_excel_sheet(writer, pd.DataFrame(_missing_by_workstream(curated)), "missing_by_workstream")
    with pd.ExcelWriter(output_dir / "NUTEV_PRISMA_FLOW_CORRIGIDO.xlsx") as writer:
        write_excel_sheet(writer, pd.DataFrame(prisma, columns=PRISMA_COLUMNS), "flow")
        write_excel_sheet(writer, pd.DataFrame([{"nota": "Operational curation summary."}]), "notes")
    summary = {
        "raw_records": len(curated),
        "unique_documents": len(unique),
        "duplicates_removed": max(len(curated) - len(unique), 0),
        "full_text_documents": sum(1 for row in unique if bool(row.get("has_full_text"))),
        "metadata_only_documents": sum(1 for row in unique if bool(row.get("is_metadata_only"))),
        "prioritized_documents": sum(1 for row in unique if bool(row.get("is_prioritized"))),
    }
    (output_dir / "curation_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary
