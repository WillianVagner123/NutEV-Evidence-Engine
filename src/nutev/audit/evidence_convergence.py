from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from nutev.export.excel_writer import write_excel_file


def _listish(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v)]
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return []
    if text.startswith("[") and text.endswith("]"):
        return [x.strip().strip("'\"") for x in text.strip("[]").split(",") if x.strip()]
    return [x.strip() for x in text.replace(";", ",").split(",") if x.strip()]


def _claim_dict(item: Any) -> dict[str, Any]:
    if hasattr(item, "model_dump"):
        return item.model_dump()
    return dict(item)


def calculate_recommendation_convergence(candidate: Any, claims: list[Any]) -> dict[str, Any]:
    c = _claim_dict(candidate)
    supporting_ids = set(_listish(c.get("supporting_claim_ids")))
    linked = [_claim_dict(x) for x in claims if _claim_dict(x).get("claim_id") in supporting_ids]
    documents = {x.get("document_id") for x in linked if x.get("document_id")}
    lenses = {lens for x in linked for lens in _listish(x.get("evidence_lenses"))}
    evidence_types = {x.get("evidence_type") for x in linked if x.get("evidence_type")}
    conflict = bool(_listish(c.get("conflicting_claim_ids")))
    score = len(documents) + len(lenses) + len(evidence_types)
    if conflict:
        score = max(0, score - 2)
    return {
        "recommendation_id": c.get("recommendation_id"),
        "protocol_component": c.get("protocol_component"),
        "supporting_claims_count": len(linked),
        "supporting_documents_count": len(documents),
        "evidence_lenses_count": len(lenses),
        "evidence_types_count": len(evidence_types),
        "conflict_flag": conflict,
        "convergence_score": score,
        "requires_adjudication": conflict,
    }


def build_convergence_tables(claims: list[Any], recommendations: list[Any]) -> dict[str, pd.DataFrame]:
    claim_rows = [_claim_dict(c) for c in claims]
    rec_rows = [_claim_dict(r) for r in recommendations]
    by_domain: dict[str, dict[str, Any]] = defaultdict(lambda: {"domain": "", "claims": 0, "documents": set(), "lenses": set()})
    for c in claim_rows:
        for domain in _listish(c.get("nutev_domains")) or ["unspecified"]:
            row = by_domain[domain]
            row["domain"] = domain
            row["claims"] += 1
            if c.get("document_id"):
                row["documents"].add(c.get("document_id"))
            row["lenses"].update(_listish(c.get("evidence_lenses")))
    domain_rows = []
    for row in by_domain.values():
        domain_rows.append({"domain": row["domain"], "claims": row["claims"], "documents": len(row["documents"]), "lenses": len(row["lenses"]), "convergence_score": row["claims"] + len(row["documents"]) + len(row["lenses"])})
    rec_conv = [calculate_recommendation_convergence(r, claims) for r in rec_rows]
    gaps = [r for r in rec_conv if r.get("supporting_claims_count", 0) == 0 or r.get("conflict_flag")]
    return {
        "convergence_by_domain": pd.DataFrame(domain_rows),
        "convergence_by_recommendation": pd.DataFrame(rec_conv),
        "gaps_and_conflicts": pd.DataFrame(gaps),
    }


def export_evidence_convergence_matrix(claims: list[Any], recommendations: list[Any], tables_dir: Path) -> dict[str, int]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    tables = build_convergence_tables(claims, recommendations)
    path = tables_dir / "NUTEV_EVIDENCE_CONVERGENCE_MATRIX.xlsx"
    try:
        with pd.ExcelWriter(path) as writer:
            for name, df in tables.items():
                df.to_excel(writer, sheet_name=name[:31], index=False)
    except Exception:
        for name, df in tables.items():
            write_excel_file(df, tables_dir / f"NUTEV_EVIDENCE_CONVERGENCE_MATRIX_{name}.xlsx")
    return {name: len(df) for name, df in tables.items()}
