"""First-class finalization of the curated layer (audit + legacy QA reports).

Phase 2 of ``docs/REFACTOR_RUNTIME_COMPAT_MIGRATION.md``. This is exactly what the
former ``runtime_compat._patch_curation`` wrapper did *after* the base
``curate_outputs`` — the ``NUTEV_*`` CSV renames, the QA / PRISMA legacy reports,
and the audit + convergence stage — but as an explicit, importable step the
pipeline calls directly instead of a monkey-patch. ``audit_metrics`` likewise
replaces ``_patch_run_summary``'s injection of claim/recommendation counts.

Behavior is unchanged: the same helpers run in the same order producing the same
artifacts; the query-parity and curation tests prove it.
"""
from __future__ import annotations

import csv
import shutil
from pathlib import Path

from nutev.export.audit_artifacts import write_audit_and_convergence

_METHODOLOGICAL_NOTE = (
    "RecommendationCandidate is not a final protocol recommendation and requires human review."
)


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _count_csv(path: Path) -> int:
    return len(_read_csv(path))


def _count_csv_where(path: Path, column: str, value: str) -> int:
    return sum(1 for row in _read_csv(path) if str(row.get(column, "")).strip() == value)


def _count_csv_truthy(path: Path, column: str) -> int:
    return sum(1 for row in _read_csv(path) if _truthy(row.get(column)))


def _copy_if_exists(source: Path, target: Path) -> None:
    if source.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def audit_metrics(tables_dir: Path) -> dict[str, int]:
    """Claim/recommendation/conflict counts read from the written audit CSVs.

    Replaces ``runtime_compat._patch_run_summary``; call it before writing
    ``run_summary.json`` and merge the result into the summary."""
    claims = tables_dir / "NUTEV_EVIDENCE_CLAIMS.csv"
    recs = tables_dir / "NUTEV_RECOMMENDATION_CANDIDATES.csv"
    conflicts = tables_dir / "NUTEV_CONFLICTS.csv"
    return {
        "evidence_claims_total": _count_csv(claims),
        "evidence_claims_supported": _count_csv_where(claims, "claim_status", "supported"),
        "evidence_claims_inference_only": _count_csv_where(claims, "claim_status", "inference_only"),
        "evidence_claims_needs_review": _count_csv_truthy(claims, "needs_human_review"),
        "recommendation_candidates_total": _count_csv(recs),
        "recommendation_candidates_ready_review": _count_csv_where(recs, "recommendation_status", "ready_for_human_review"),
        "recommendation_candidates_insufficient_evidence": _count_csv_where(recs, "recommendation_status", "insufficient_evidence") + _count_csv_where(recs, "recommendation_status", "draft_needs_evidence"),
        "conflicting_evidence_total": _count_csv(conflicts),
    }


def _legacy_reports(rows: list[dict], output_dir: Path, unique_documents: int) -> dict[str, int]:
    import pandas as pd

    curated = _read_csv(output_dir / "curated_metadata.csv")
    raw_records = len(rows)
    duplicate_rows = max(0, raw_records - unique_documents)
    groups: dict[str, list[dict]] = {}
    for row in curated:
        groups.setdefault(str(row.get("document_key", "")), []).append(row)
    duplicate_documents = sum(1 for group in groups.values() if len(group) > 1)

    duplicate_summary = []
    for group in groups.values():
        if len(group) > 1:
            key_type = str(group[0].get("document_key_type", "")) or "unknown"
            duplicate_summary.append({"document_key_type": key_type, "duplicate_documents": 1, "duplicate_rows": len(group)})
    if not duplicate_summary:
        duplicate_summary = [{"document_key_type": "none", "duplicate_documents": 0, "duplicate_rows": 0}]

    by_ws: dict[str, dict[str, int | str]] = {}
    for row in curated:
        ws = str(row.get("workstream", "") or "unknown")
        item = by_ws.setdefault(ws, {"workstream": ws, "missing_title": 0, "missing_url": 0, "missing_year": 0, "missing_evidence_type": 0})
        item["missing_title"] = int(item["missing_title"]) + int(not str(row.get("title", "")).strip())
        item["missing_url"] = int(item["missing_url"]) + int(not (str(row.get("final_url", "")).strip() or str(row.get("original_url", "")).strip()))
        item["missing_year"] = int(item["missing_year"]) + int(not str(row.get("year", "")).strip())
        item["missing_evidence_type"] = int(item["missing_evidence_type"]) + int(not str(row.get("evidence_type", "")).strip())
    missing_rows = list(by_ws.values()) or [{"workstream": "none", "missing_title": 0, "missing_url": 0, "missing_year": 0, "missing_evidence_type": 0}]

    prisma_path = output_dir / "NUTEV_PRISMA_FLOW_CORRIGIDO.xlsx"
    qa_path = output_dir / "NUTEV_QA_REPORT.xlsx"
    prisma_df = pd.DataFrame([{"registros_identificados": raw_records, "duplicados_removidos": duplicate_rows, "registros_triados": unique_documents, "documentos_com_pdf_ou_html": sum(1 for r in curated if _truthy(str(r.get("has_full_text", "")))), "documentos_metadata_only": sum(1 for r in curated if _truthy(str(r.get("is_metadata_only", "")))), "documentos_priorizados": sum(1 for r in curated if _truthy(str(r.get("is_prioritized", ""))))}])
    try:
        with pd.ExcelWriter(prisma_path) as writer:
            prisma_df.to_excel(writer, sheet_name="flow", index=False)
    except Exception:
        prisma_df.to_csv(prisma_path.with_suffix(".flow.csv"), index=False, encoding="utf-8-sig")
        prisma_path.touch()
    try:
        with pd.ExcelWriter(qa_path) as writer:
            pd.DataFrame([{"metric": "raw_records", "value": raw_records}, {"metric": "unique_documents", "value": unique_documents}, {"metric": "duplicate_documents", "value": duplicate_documents}, {"metric": "duplicate_rows", "value": duplicate_rows}]).to_excel(writer, sheet_name="summary", index=False)
            pd.DataFrame(duplicate_summary).to_excel(writer, sheet_name="duplicate_summary", index=False)
            pd.DataFrame(missing_rows).to_excel(writer, sheet_name="missing_by_workstream", index=False)
    except Exception:
        pd.DataFrame(duplicate_summary).to_csv(qa_path.with_suffix(".duplicate_summary.csv"), index=False, encoding="utf-8-sig")
        pd.DataFrame(missing_rows).to_csv(qa_path.with_suffix(".missing_by_workstream.csv"), index=False, encoding="utf-8-sig")
        qa_path.touch()
    return {"raw_records": raw_records, "duplicate_rows": duplicate_rows, "duplicate_documents": duplicate_documents}


def finalize_curated_layer(rows: list[dict], output_dir: Path, curation_summary: dict) -> dict:
    """Post-curation finalization: NUTEV_* CSV renames, legacy QA reports, and the
    audit + convergence stage. Mutates and returns ``curation_summary`` with the
    same setdefault/update semantics the former ``_patch_curation`` wrapper used
    (so a base key like ``curated_rows`` is preserved, legacy/audit keys overwrite),
    keeping the finalized summary byte-identical to the patched behaviour."""
    output_dir = Path(output_dir)
    unique_documents = int(curation_summary.get("unique_documents", 0))
    _copy_if_exists(output_dir / "curated_metadata.csv", output_dir / "NUTEV_METADATA_CURATED.csv")
    _copy_if_exists(output_dir / "unique_documents.csv", output_dir / "NUTEV_DOCUMENTS_UNIQUE.csv")
    _copy_if_exists(output_dir / "workstream_document_map.csv", output_dir / "NUTEV_DOCUMENT_WORKSTREAM_MAP.csv")
    curation_summary.update(_legacy_reports(rows, output_dir, unique_documents))
    curation_summary.setdefault("input_rows", len(rows))
    curation_summary.setdefault("curated_rows", len(rows))
    try:
        curation_summary.update(
            write_audit_and_convergence(rows, output_dir.parent / "02_metadata", output_dir.parent / "06_tables")
        )
        curation_summary["methodological_note"] = _METHODOLOGICAL_NOTE
    except Exception as exc:  # never abort a run on an audit hiccup (matches the old patch)
        curation_summary.setdefault("audit_artifact_error", str(exc))
    return curation_summary
