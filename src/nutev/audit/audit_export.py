from __future__ import annotations

from pathlib import Path
import pandas as pd

from nutev.audit.models import AuditEvent, ClaimEvaluation, EvidenceClaim, RecommendationCandidate
from nutev.export.excel_writer import write_excel_sheet
from nutev.export.excel_writer import write_excel_file
from nutev.export.metadata_tables import write_simple_csv


def _df(items):
    return pd.DataFrame([i.model_dump() for i in items])


def export_audit_outputs(
    claims: list[EvidenceClaim],
    evaluations: list[ClaimEvaluation],
    recommendations: list[RecommendationCandidate],
    audit_events: list[AuditEvent],
    conflicts: list[dict],
    tables_dir: Path,
    metadata_dir: Path,
) -> None:
    tables_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    claims_df = _df(claims)
    rec_df = _df(recommendations)
    events_df = _df(audit_events)
    conflicts_df = pd.DataFrame(conflicts)

    try:
        with pd.ExcelWriter(tables_dir / "NUTEV_EVIDENCE_CLAIMS.xlsx") as writer:
            write_excel_sheet(writer, claims_df, "all_claims")
            write_excel_sheet(writer, claims_df[claims_df.get("claim_status", "") == "supported"], "supported_claims")
            write_excel_sheet(writer, claims_df[claims_df.get("claim_status", "") == "needs_human_review"], "needs_human_review")
            write_excel_sheet(writer, claims_df[claims_df.get("claim_status", "") == "inference_only"], "inference_only")
            write_excel_sheet(writer, claims_df[claims_df.get("claim_status", "") == "insufficient_evidence"], "insufficient_evidence")
            write_excel_sheet(writer, claims_df[claims_df.get("claim_status", "") == "conflicting"], "conflicting_claims")
    except Exception:
        write_excel_file(claims_df, tables_dir / "NUTEV_EVIDENCE_CLAIMS.xlsx")

    try:
        with pd.ExcelWriter(tables_dir / "NUTEV_RECOMMENDATION_CANDIDATES.xlsx") as writer:
            write_excel_sheet(writer, rec_df, "all_candidates")
            for s in ["ready_for_human_review", "insufficient_evidence", "conflicting_evidence", "approved_for_protocol", "rejected"]:
                write_excel_sheet(writer, rec_df[rec_df.get("recommendation_status", "") == s], s)
    except Exception:
        write_excel_file(rec_df, tables_dir / "NUTEV_RECOMMENDATION_CANDIDATES.xlsx")

    write_excel_file(events_df, tables_dir / "NUTEV_RECOMMENDATION_AUDIT_TRAIL.xlsx")
    write_excel_file(claims_df[claims_df.get("claim_status", "") == "insufficient_evidence"], tables_dir / "NUTEV_UNSUPPORTED_CLAIMS.xlsx")
    write_excel_file(conflicts_df, tables_dir / "NUTEV_CONFLICTING_EVIDENCE.xlsx")
    write_excel_file(claims_df[claims_df.get("needs_human_review", False) == True], tables_dir / "NUTEV_HUMAN_REVIEW_QUEUE.xlsx")

    write_simple_csv(claims_df.to_dict("records"), metadata_dir / "NUTEV_EVIDENCE_CLAIMS.csv")
    write_simple_csv(rec_df.to_dict("records"), metadata_dir / "NUTEV_RECOMMENDATION_CANDIDATES.csv")
    write_simple_csv(events_df.to_dict("records"), metadata_dir / "NUTEV_RECOMMENDATION_AUDIT_TRAIL.csv")
