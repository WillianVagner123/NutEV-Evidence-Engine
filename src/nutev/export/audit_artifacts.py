from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd

from nutev.audit.claim_evaluator import detect_conflicts, evaluate_claims
from nutev.audit.claim_extractor import extract_candidate_claims_from_record
from nutev.audit.models import EvidenceClaim, RecommendationCandidate
from nutev.engine.ids import make_document_id
from nutev.export.excel_writer import sanitize_dataframe_for_excel

_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


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


def _list(value: object) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [_text(v) for v in value if _text(v)]
    if isinstance(value, (tuple, set)):
        return [_text(v) for v in value if _text(v)]
    text = _text(value)
    if ";" in text:
        return [part.strip() for part in text.split(";") if part.strip()]
    return [text] if text else []


def _year(value: object) -> int | None:
    match = _YEAR_RE.search(_text(value))
    return int(match.group(0)) if match else None


def _rows(items: list[object]) -> list[dict]:
    rows: list[dict] = []
    for item in items:
        if hasattr(item, "model_dump"):
            rows.append(item.model_dump(mode="json"))  # type: ignore[attr-defined]
        elif isinstance(item, dict):
            rows.append(item)
    return rows


def _write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sanitize_dataframe_for_excel(pd.DataFrame(rows)).to_csv(path, index=False, encoding="utf-8-sig")


def _claim_record(row: dict) -> dict:
    record = dict(row)
    if not _text(record.get("document_id")):
        record["document_id"] = make_document_id(record)
    record["url"] = record.get("url") or record.get("final_url") or record.get("original_url")
    record["clinical_conditions"] = _list(record.get("clinical_conditions"))
    record["diet_patterns"] = _list(record.get("diet_patterns"))
    record["outcomes"] = _list(record.get("outcomes"))
    record["evidence_lenses"] = _list(record.get("evidence_lenses"))
    record["year"] = _year(record.get("year"))
    return record


def extract_audit_claims(rows: list[dict]) -> list[EvidenceClaim]:
    claims: list[EvidenceClaim] = []
    for row in rows:
        try:
            claims.extend(extract_candidate_claims_from_record(_claim_record(row), {}, {}))
        except Exception:
            continue
    return claims


def build_recommendation_candidates(claims: list[EvidenceClaim], conflicts: list[dict]) -> list[RecommendationCandidate]:
    conflict_ids = {
        value
        for conflict in conflicts
        for key, value in conflict.items()
        if key.startswith("claim_id") and isinstance(value, str) and value
    }
    grouped: dict[str, list[EvidenceClaim]] = {}
    for claim in claims:
        if claim.claim_status not in {"supported", "partially_supported"}:
            continue
        for component in claim.protocol_components or claim.nutev_domains or ["geral_nutev"]:
            grouped.setdefault(component, []).append(claim)

    candidates: list[RecommendationCandidate] = []
    for component, component_claims in sorted(grouped.items()):
        supporting_claim_ids = sorted({claim.claim_id for claim in component_claims})
        conflicting_claim_ids = sorted(set(supporting_claim_ids) & conflict_ids)
        digest = hashlib.sha1(f"{component}|{'|'.join(supporting_claim_ids)}".encode("utf-8")).hexdigest()[:16]  # noqa: S324
        candidates.append(
            RecommendationCandidate(
                recommendation_id=f"rec_{digest}",
                recommendation_text=(
                    f"Revisar o componente '{component}' para o protocolo NutEV/NutMEV "
                    "com base nas claims documentais vinculadas."
                ),
                protocol_component=component,
                nutev_domains=sorted({d for claim in component_claims for d in claim.nutev_domains}),
                supporting_claim_ids=supporting_claim_ids,
                supporting_document_ids=sorted({claim.document_id for claim in component_claims if claim.document_id}),
                conflicting_claim_ids=conflicting_claim_ids,
                evidence_lenses=sorted({lens for claim in component_claims for lens in claim.evidence_lenses}),
                clinical_conditions=sorted({c for claim in component_claims for c in claim.clinical_conditions}),
                dietary_patterns=sorted({p for claim in component_claims for p in claim.dietary_patterns}),
                outcomes=sorted({o for claim in component_claims for o in claim.outcomes}),
                strength_placeholder="requires_human_adjudication",
                evidence_gap="Conflito detectado; requer revisão humana." if conflicting_claim_ids else None,
                recommendation_status="conflicting_evidence" if conflicting_claim_ids else "ready_for_human_review",
                human_approval_status="not_reviewed",
            )
        )
    return candidates


def _compute_audit(rows: list[dict]):
    """Derive claims → evaluations → conflicts → recommendations from pipeline rows."""
    claims = extract_audit_claims(rows)
    evaluations = evaluate_claims(claims, {})
    conflicts = detect_conflicts(claims)
    recommendations = build_recommendation_candidates(claims, conflicts)
    return claims, evaluations, conflicts, recommendations


def _audit_summary(claims: list, conflicts: list, recommendations: list) -> dict:
    return {
        "evidence_claims_total": len(claims),
        "evidence_claims_supported": sum(1 for claim in claims if claim.claim_status == "supported"),
        "evidence_claims_inference_only": sum(1 for claim in claims if claim.claim_status == "inference_only"),
        "evidence_claims_needs_review": sum(1 for claim in claims if claim.needs_human_review),
        "recommendation_candidates_total": len(recommendations),
        "recommendation_candidates_ready_review": sum(
            1 for rec in recommendations if rec.recommendation_status == "ready_for_human_review"
        ),
        "recommendation_candidates_insufficient_evidence": sum(
            1 for rec in recommendations if rec.recommendation_status in {"insufficient_evidence", "draft_needs_evidence"}
        ),
        "conflicting_evidence_total": len(conflicts),
    }


def _write_audit_csvs(claims, evaluations, conflicts, recommendations, out_dir: Path) -> None:
    _write_csv(_rows(claims), out_dir / "NUTEV_EVIDENCE_CLAIMS.csv")
    _write_csv(_rows(evaluations), out_dir / "NUTEV_CLAIM_EVALUATIONS.csv")
    _write_csv(conflicts, out_dir / "NUTEV_CONFLICTS.csv")
    _write_csv(_rows(recommendations), out_dir / "NUTEV_RECOMMENDATION_CANDIDATES.csv")


def write_audit_artifacts(rows: list[dict], tables_dir: Path) -> dict:
    claims, evaluations, conflicts, recommendations = _compute_audit(rows)
    _write_audit_csvs(claims, evaluations, conflicts, recommendations, Path(tables_dir))
    return _audit_summary(claims, conflicts, recommendations)


def write_audit_and_convergence(rows: list[dict], metadata_dir: Path, tables_dir: Path) -> dict:
    """First-class audit stage: claims/recs + convergence/gaps/readiness in one place.

    Audit CSVs (claims, evaluations, conflicts, recommendation candidates) go to
    ``metadata_dir`` (``02_metadata`` — where the dashboard/API/pilot report read
    them). The derived scientific matrices — evidence convergence, gap register,
    protocol readiness and locked items — go to ``tables_dir`` (``06_tables`` —
    where the dashboard reads them). Before this, those matrices were produced
    only by ``nutev demo-data``, so a real run left the dashboard's
    convergence/gap/readiness panels empty (audit finding C3).

    A failure in the derived matrices is recorded in the returned summary
    (``convergence_stage_error``) — surfaced in run_summary.json, never swallowed
    silently — and never blocks the audit CSVs the UI needs most.
    """
    metadata_dir = Path(metadata_dir)
    tables_dir = Path(tables_dir)
    claims, evaluations, conflicts, recommendations = _compute_audit(rows)
    _write_audit_csvs(claims, evaluations, conflicts, recommendations, metadata_dir)
    summary = _audit_summary(claims, conflicts, recommendations)

    claim_records = _rows(claims)
    rec_records = _rows(recommendations)
    try:
        from nutev.audit.evidence_convergence import export_evidence_convergence_matrix
        from nutev.audit.gap_register import export_evidence_gap_register
        from nutev.protocol.locked_items import export_locked_protocol_items
        from nutev.protocol.readiness import (
            build_protocol_readiness_matrix,
            export_protocol_readiness_matrix,
        )

        convergence = export_evidence_convergence_matrix(claim_records, rec_records, tables_dir)
        gaps_total = export_evidence_gap_register(claim_records, rec_records, conflicts, tables_dir)
        ready_total = export_protocol_readiness_matrix(rec_records, claim_records, tables_dir)
        readiness_df = build_protocol_readiness_matrix(rec_records, claim_records)
        locked_total = export_locked_protocol_items(rec_records, readiness_df, tables_dir)
        summary.update({
            "evidence_convergence_total": sum(convergence.values()) if isinstance(convergence, dict) else 0,
            "evidence_gaps_total": gaps_total,
            "protocol_ready_total": ready_total,
            "locked_protocol_items_total": locked_total,
        })
    except Exception as exc:  # surfaced in summary, not swallowed
        summary["convergence_stage_error"] = str(exc)
    return summary
