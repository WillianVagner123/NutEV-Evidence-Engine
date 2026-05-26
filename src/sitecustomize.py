from __future__ import annotations

"""Runtime compatibility hooks for NutEV/NutMEV local executions.

This module is imported automatically by Python when ``src`` is on
``PYTHONPATH``. It keeps the current pipeline compatible while the canonical
pipeline is being incrementally upgraded.
"""

import csv
import shutil
from pathlib import Path
from typing import Any


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _count_csv(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return sum(1 for _ in reader)


def _count_csv_where(path: Path, column: str, value: str) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if str(row.get(column, "")).strip() == value:
                count += 1
    return count


def _count_csv_truthy(path: Path, column: str) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if _truthy(row.get(column)):
                count += 1
    return count


def _audit_metrics(tables_dir: Path) -> dict[str, int]:
    claims = tables_dir / "NUTEV_EVIDENCE_CLAIMS.csv"
    recs = tables_dir / "NUTEV_RECOMMENDATION_CANDIDATES.csv"
    conflicts = tables_dir / "NUTEV_CONFLICTS.csv"
    return {
        "evidence_claims_total": _count_csv(claims),
        "evidence_claims_supported": _count_csv_where(claims, "claim_status", "supported"),
        "evidence_claims_needs_review": _count_csv_truthy(claims, "needs_human_review"),
        "recommendation_candidates_total": _count_csv(recs),
        "recommendation_candidates_ready_review": _count_csv_where(
            recs, "recommendation_status", "ready_for_human_review"
        ),
        "recommendation_candidates_insufficient_evidence": (
            _count_csv_where(recs, "recommendation_status", "insufficient_evidence")
            + _count_csv_where(recs, "recommendation_status", "draft_needs_evidence")
        ),
        "conflicting_evidence_total": _count_csv(conflicts),
    }


def _copy_if_exists(source: Path, target: Path) -> None:
    if source.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_legacy_curation_reports(rows: list[dict], output_dir: Path, unique_documents: int) -> dict[str, int]:
    import pandas as pd

    curated_rows = _read_csv(output_dir / "curated_metadata.csv")
    raw_records = len(rows)
    duplicate_rows = max(0, raw_records - unique_documents)
    duplicate_documents = 0
    if curated_rows:
        groups: dict[str, list[dict]] = {}
        for row in curated_rows:
            groups.setdefault(str(row.get("document_key", "")), []).append(row)
        duplicate_documents = sum(1 for values in groups.values() if len(values) > 1)
        duplicate_key_types: dict[str, dict[str, int]] = {}
        for values in groups.values():
            if len(values) <= 1:
                continue
            key_type = str(values[0].get("document_key_type", "")) or "unknown"
            bucket = duplicate_key_types.setdefault(
                key_type,
                {"document_key_type": key_type, "duplicate_documents": 0, "duplicate_rows": 0},
            )
            bucket["duplicate_documents"] += 1
            bucket["duplicate_rows"] += len(values)
        duplicate_summary_rows = list(duplicate_key_types.values()) or [
            {"document_key_type": "none", "duplicate_documents": 0, "duplicate_rows": 0}
        ]
    else:
        duplicate_summary_rows = [
            {"document_key_type": "none", "duplicate_documents": 0, "duplicate_rows": 0}
        ]

    by_ws: dict[str, dict[str, int | str]] = {}
    for row in curated_rows:
        ws = str(row.get("workstream", "") or "unknown")
        bucket = by_ws.setdefault(
            ws,
            {
                "workstream": ws,
                "missing_title": 0,
                "missing_url": 0,
                "missing_year": 0,
                "missing_evidence_type": 0,
            },
        )
        if not str(row.get("title", "")).strip():
            bucket["missing_title"] = int(bucket["missing_title"]) + 1
        if not (str(row.get("final_url", "")).strip() or str(row.get("original_url", "")).strip()):
            bucket["missing_url"] = int(bucket["missing_url"]) + 1
        if not str(row.get("year", "")).strip():
            bucket["missing_year"] = int(bucket["missing_year"]) + 1
        if not str(row.get("evidence_type", "")).strip():
            bucket["missing_evidence_type"] = int(bucket["missing_evidence_type"]) + 1

    missing_rows = list(by_ws.values()) or [
        {
            "workstream": "none",
            "missing_title": 0,
            "missing_url": 0,
            "missing_year": 0,
            "missing_evidence_type": 0,
        }
    ]

    prisma = pd.DataFrame(
        [
            {
                "registros_identificados": raw_records,
                "duplicados_removidos": duplicate_rows,
                "registros_triados": unique_documents,
                "documentos_com_pdf_ou_html": sum(
                    1 for row in curated_rows if _truthy(str(row.get("has_full_text", "")))
                ),
                "documentos_metadata_only": sum(
                    1 for row in curated_rows if _truthy(str(row.get("is_metadata_only", "")))
                ),
                "documentos_priorizados": sum(
                    1 for row in curated_rows if _truthy(str(row.get("is_prioritized", "")))
                ),
            }
        ]
    )
    with pd.ExcelWriter(output_dir / "NUTEV_PRISMA_FLOW_CORRIGIDO.xlsx") as writer:
        prisma.to_excel(writer, sheet_name="flow", index=False)
    with pd.ExcelWriter(output_dir / "NUTEV_QA_REPORT.xlsx") as writer:
        pd.DataFrame(
            [
                {"metric": "raw_records", "value": raw_records},
                {"metric": "unique_documents", "value": unique_documents},
                {"metric": "duplicate_documents", "value": duplicate_documents},
                {"metric": "duplicate_rows", "value": duplicate_rows},
            ]
        ).to_excel(writer, sheet_name="summary", index=False)
        pd.DataFrame(duplicate_summary_rows).to_excel(writer, sheet_name="duplicate_summary", index=False)
        pd.DataFrame(missing_rows).to_excel(writer, sheet_name="missing_by_workstream", index=False)

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

    def curate_outputs_with_audit(rows: list[dict], output_dir: Path) -> dict[str, Any]:
        output_dir = Path(output_dir)
        summary = original(rows, output_dir)
        unique_documents = int(summary.get("unique_documents", 0))
        _copy_if_exists(output_dir / "curated_metadata.csv", output_dir / "NUTEV_METADATA_CURATED.csv")
        _copy_if_exists(output_dir / "unique_documents.csv", output_dir / "NUTEV_DOCUMENTS_UNIQUE.csv")
        _copy_if_exists(output_dir / "workstream_document_map.csv", output_dir / "NUTEV_DOCUMENT_WORKSTREAM_MAP.csv")
        legacy_summary = _write_legacy_curation_reports(rows, output_dir, unique_documents)
        summary.setdefault("input_rows", len(rows))
        summary.setdefault("curated_rows", len(rows))
        summary["raw_records"] = legacy_summary["raw_records"]
        summary["duplicate_rows"] = legacy_summary["duplicate_rows"]
        summary["duplicate_documents"] = legacy_summary["duplicate_documents"]
        try:
            audit_summary = write_audit_artifacts(rows, output_dir.parent / "06_tables")
            summary.update(audit_summary)
            summary["methodological_note"] = (
                "RecommendationCandidate is not a final protocol recommendation and requires human review."
            )
        except Exception as exc:
            summary.setdefault("audit_artifact_error", str(exc))
        return summary

    curate_outputs_with_audit._nutev_audit_patched = True  # type: ignore[attr-defined]
    curation_module.curate_outputs = curate_outputs_with_audit


def _patch_run_summary() -> None:
    try:
        from nutev.export import logs as logs_module
    except Exception:
        return

    original = getattr(logs_module, "write_run_summary", None)
    if original is None or getattr(original, "_nutev_audit_patched", False):
        return

    def write_run_summary_with_audit(path: Path, summary: dict) -> None:
        path = Path(path)
        tables_dir = path.parent.parent / "06_tables"
        metrics = _audit_metrics(tables_dir)
        for key, value in metrics.items():
            if value or key not in summary:
                summary[key] = value
        original(path, summary)

    write_run_summary_with_audit._nutev_audit_patched = True  # type: ignore[attr-defined]
    logs_module.write_run_summary = write_run_summary_with_audit


def _patch_workstream_validation() -> None:
    try:
        from nutev.engine import models as models_module
        from nutev.engine import validators as validators_module
    except Exception:
        return

    original = getattr(validators_module, "validate_workstream", None)
    if original is None or getattr(original, "_nutev_global_watch_patched", False):
        return

    def validate_workstream_patched(value: str | None) -> str | None:
        if value in (None, ""):
            return None
        normalized = str(value).strip()
        if normalized == "global_watch":
            return normalized
        return original(value)

    validate_workstream_patched._nutev_global_watch_patched = True  # type: ignore[attr-defined]
    validators_module.validate_workstream = validate_workstream_patched
    models_module.validate_workstream = validate_workstream_patched


def _patch_synthesis_defaults() -> None:
    try:
        from nutev.analysis import synthesis as synthesis_module
    except Exception:
        return

    original = getattr(synthesis_module, "write_synthesis_outputs", None)
    if original is None or getattr(original, "_nutev_defaults_patched", False):
        return

    defaults = {
        "evidence_priority_score": 0,
        "evidence_priority_tier": "unclassified",
        "evidence_use_track": "unclassified",
        "evidence_use_primary": "",
        "evidence_use_secondary": "",
        "reading_lane": "standard",
    }

    def write_synthesis_outputs_patched(master_rows: list[dict], out_dir: Path) -> None:
        patched_rows = []
        for row in master_rows:
            item = dict(row)
            for key, value in defaults.items():
                item.setdefault(key, value)
            patched_rows.append(item)
        return original(patched_rows, out_dir)

    write_synthesis_outputs_patched._nutev_defaults_patched = True  # type: ignore[attr-defined]
    synthesis_module.write_synthesis_outputs = write_synthesis_outputs_patched


def _patch_query_generation() -> None:
    try:
        from nutev.querypacks import builders as builders_module
        from nutev.querypacks import provider_queries as provider_module
    except Exception:
        return

    original_render = getattr(provider_module, "render_queries_for_provider", None)
    if original_render is not None and not getattr(original_render, "_nutev_terms_patched", False):
        def render_queries_for_provider_patched(keyword_taxonomy: dict, workstream: str, provider: str) -> list[str]:
            queries = list(original_render(keyword_taxonomy, workstream, provider))
            if provider == "pubmed":
                ws = builders_module.canonical_workstream(workstream)
                if ws == "busca2a":
                    queries.extend([
                        '"therapeutic lifestyle changes"[Title/Abstract]',
                        '"living guideline"[Title/Abstract]',
                    ])
                if ws == "busca2b":
                    queries.extend([
                        '"medical nutrition therapy"[Title/Abstract]',
                        '"steatotic liver disease"[Title/Abstract]',
                        '"ketogenic diet"[Title/Abstract]',
                        '"network meta-analysis"[Title/Abstract]',
                    ])
            return builders_module.uniq([q for q in queries if q])

        render_queries_for_provider_patched._nutev_terms_patched = True  # type: ignore[attr-defined]
        provider_module.render_queries_for_provider = render_queries_for_provider_patched

    original_build = getattr(builders_module, "build_queries", None)
    if original_build is not None and not getattr(original_build, "_nutev_foodmed_patched", False):
        def build_queries_patched(keyword_taxonomy: dict, workstream: str) -> list[str]:
            queries = list(original_build(keyword_taxonomy, workstream))
            ws = builders_module.canonical_workstream(workstream)
            if ws == "busca2b":
                queries.append('("food is medicine" OR "produce prescription" OR "medically tailored meals")')
            return builders_module.uniq([q for q in queries if q])

        build_queries_patched._nutev_foodmed_patched = True  # type: ignore[attr-defined]
        builders_module.build_queries = build_queries_patched


_patch_workstream_validation()
_patch_curation()
_patch_run_summary()
_patch_synthesis_defaults()
_patch_query_generation()
