from __future__ import annotations

"""Runtime compatibility hooks for NutEV/NutMEV local executions.

This module is imported automatically by Python when ``src`` is on
``PYTHONPATH``. It keeps the current pipeline compatible while the canonical
pipeline is being incrementally upgraded.
"""

import csv
import os
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
        summary = original(rows, output_dir)
        try:
            audit_summary = write_audit_artifacts(rows, Path(output_dir).parent / "06_tables")
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


_patch_curation()
_patch_run_summary()
