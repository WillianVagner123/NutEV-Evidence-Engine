from __future__ import annotations

"""Runtime compatibility hooks for NutEV/NutMEV local executions.

These hooks wrap a handful of pipeline functions (curation, run-summary,
synthesis defaults, query generation, workstream validation) so that a local
run emits the full audit/legacy artifact set. They MUST be applied
deterministically: call :func:`apply` from an explicit entrypoint (the ``nutev``
CLI does this) instead of relying on ``sitecustomize.py`` being auto-imported,
which only happens when no other ``sitecustomize`` shadows it on ``sys.path``.
Every patch is idempotent, so calling :func:`apply` more than once is safe.
"""

import csv
import shutil
from pathlib import Path
from typing import Any


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


def _audit_metrics(tables_dir: Path) -> dict[str, int]:
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


def _copy_if_exists(source: Path, target: Path) -> None:
    if source.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


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


def _patch_curation() -> None:
    try:
        from nutev.export import curation as curation_module
        from nutev.export.audit_artifacts import write_audit_artifacts
    except Exception:
        return
    original = getattr(curation_module, "curate_outputs", None)
    if original is None or getattr(original, "_nutev_audit_patched", False):
        return

    def wrapped(rows: list[dict], output_dir: Path) -> dict[str, Any]:
        output_dir = Path(output_dir)
        summary = original(rows, output_dir)
        unique_documents = int(summary.get("unique_documents", 0))
        _copy_if_exists(output_dir / "curated_metadata.csv", output_dir / "NUTEV_METADATA_CURATED.csv")
        _copy_if_exists(output_dir / "unique_documents.csv", output_dir / "NUTEV_DOCUMENTS_UNIQUE.csv")
        _copy_if_exists(output_dir / "workstream_document_map.csv", output_dir / "NUTEV_DOCUMENT_WORKSTREAM_MAP.csv")
        summary.update(_legacy_reports(rows, output_dir, unique_documents))
        summary.setdefault("input_rows", len(rows))
        summary.setdefault("curated_rows", len(rows))
        try:
            summary.update(write_audit_artifacts(rows, output_dir.parent / "06_tables"))
            summary["methodological_note"] = "RecommendationCandidate is not a final protocol recommendation and requires human review."
        except Exception as exc:
            summary.setdefault("audit_artifact_error", str(exc))
        return summary

    wrapped._nutev_audit_patched = True  # type: ignore[attr-defined]
    curation_module.curate_outputs = wrapped


def _patch_run_summary() -> None:
    try:
        from nutev.export import logs as logs_module
    except Exception:
        return
    original = getattr(logs_module, "write_run_summary", None)
    if original is None or getattr(original, "_nutev_audit_patched", False):
        return

    def wrapped(path: Path, summary: dict) -> None:
        path = Path(path)
        for key, value in _audit_metrics(path.parent.parent / "06_tables").items():
            if value or key not in summary:
                summary[key] = value
        original(path, summary)

    wrapped._nutev_audit_patched = True  # type: ignore[attr-defined]
    logs_module.write_run_summary = wrapped


def _patch_workstream_validation() -> None:
    try:
        from nutev.engine import models as models_module
        from nutev.engine import validators as validators_module
    except Exception:
        return
    original = getattr(validators_module, "validate_workstream", None)
    if original is None or getattr(original, "_nutev_global_watch_patched", False):
        return

    def wrapped(value: str | None) -> str | None:
        if value in (None, ""):
            return None
        normalized = str(value).strip()
        if normalized == "global_watch":
            return normalized
        return original(value)

    wrapped._nutev_global_watch_patched = True  # type: ignore[attr-defined]
    validators_module.validate_workstream = wrapped
    models_module.validate_workstream = wrapped


def _patch_synthesis_defaults() -> None:
    try:
        from nutev.analysis import synthesis as synthesis_module
    except Exception:
        return
    original = getattr(synthesis_module, "write_synthesis_outputs", None)
    if original is None or getattr(original, "_nutev_defaults_patched", False):
        return
    defaults = {"evidence_priority_score": 0, "evidence_priority_tier": "unclassified", "evidence_use_track": "unclassified", "evidence_use_primary": "", "evidence_use_secondary": "", "reading_lane": "standard"}

    def wrapped(master_rows: list[dict], out_dir: Path) -> None:
        return original([{**defaults, **dict(row)} for row in master_rows], out_dir)

    wrapped._nutev_defaults_patched = True  # type: ignore[attr-defined]
    synthesis_module.write_synthesis_outputs = wrapped


def _patch_query_generation() -> None:
    try:
        from nutev.querypacks import builders as builders_module
        from nutev.querypacks import provider_queries as provider_module
    except Exception:
        return
    original_render = getattr(provider_module, "render_queries_for_provider", None)
    if original_render is not None and not getattr(original_render, "_nutev_terms_patched", False):
        def wrapped_render(keyword_taxonomy: dict, workstream: str, provider: str) -> list[str]:
            queries = list(original_render(keyword_taxonomy, workstream, provider))
            if provider == "pubmed":
                ws = builders_module.canonical_workstream(workstream)
                if ws == "busca2a":
                    terms = ["therapeutic lifestyle changes", "mediterranean dietary pattern", "dietary approaches to stop hypertension", "DASH eating plan", "heart-healthy diet", "cardioprotective diet", "diet quality", "healthy eating pattern", "living guideline", "clinical guidance"]
                elif ws == "busca2b":
                    terms = ["medical nutrition therapy", "hybrid type 1", "hybrid type 2", "hybrid type 3", "steatotic liver disease", "metabolic dysfunction-associated steatohepatitis", "non-alcoholic fatty liver disease", "nonalcoholic steatohepatitis", "ketogenic diet", "low-carbohydrate diet", "low carbohydrate diet", "carbohydrate-restricted diet", "carbohydrate restricted diet", "DASH eating plan", "TLC diet", "therapeutic lifestyle changes diet", "heart-healthy diet", "cardioprotective diet", "diet quality", "healthy eating pattern", "network meta-analysis", "living systematic review", "rapid review", "food environment intervention", "food procurement policy", "healthy food retail", "choice architecture", "healthy default"]
                elif ws in {"busca1", "artigo3_framework"}:
                    terms = ["food environment intervention", "retail food environment", "healthy food retail", "healthy food procurement", "food procurement policy", "nutrition standards", "choice architecture", "healthy default", "menu labeling policy", "food policy implementation"]
                else:
                    terms = []
                queries.extend([f'"{term}"[Title/Abstract]' for term in terms])
            return builders_module.uniq([q for q in queries if q])

        wrapped_render._nutev_terms_patched = True  # type: ignore[attr-defined]
        provider_module.render_queries_for_provider = wrapped_render
    original_build = getattr(builders_module, "build_queries", None)
    if original_build is not None and not getattr(original_build, "_nutev_foodmed_patched", False):
        def wrapped_build(keyword_taxonomy: dict, workstream: str) -> list[str]:
            queries = list(original_build(keyword_taxonomy, workstream))
            ws = builders_module.canonical_workstream(workstream)
            if ws == "busca2b":
                queries.append('("food is medicine" OR "produce prescription" OR "medically tailored meals")')
                queries.append('("DASH eating plan" OR "TLC diet" OR "therapeutic lifestyle changes diet" OR "heart-healthy diet" OR "cardioprotective diet") AND ("obesity" OR "cardiometabolic" OR "type 2 diabetes" OR "hypertension" OR "dyslipidemia")')
                queries.append('("food environment intervention" OR "healthy food retail" OR "food procurement policy") AND ("implementation" OR "dietary adherence" OR "cardiometabolic")')
            elif ws in {"busca1", "artigo3_framework"}:
                queries.append('("food environment intervention" OR "healthy food retail" OR "healthy food procurement" OR "food procurement policy" OR "choice architecture") AND ("nutrition" OR "diet" OR "food literacy" OR "lifestyle medicine")')
            return builders_module.uniq([q for q in queries if q])

        wrapped_build._nutev_foodmed_patched = True  # type: ignore[attr-defined]
        builders_module.build_queries = wrapped_build


_APPLIED = False


def apply() -> None:
    """Apply all runtime-compat patches once. Idempotent and side-effect safe."""
    global _APPLIED
    if _APPLIED:
        return
    _patch_workstream_validation()
    _patch_curation()
    _patch_run_summary()
    _patch_synthesis_defaults()
    _patch_query_generation()
    _APPLIED = True
