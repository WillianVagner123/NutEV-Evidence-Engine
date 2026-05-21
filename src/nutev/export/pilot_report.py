from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _safe_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def generate_pilot_report(project_root: Path) -> Path:
    m = _safe_csv(project_root / "02_metadata" / "metadata_master.csv")
    c = _safe_csv(project_root / "02_metadata" / "NUTEV_EVIDENCE_CLAIMS.csv")
    r = _safe_csv(project_root / "02_metadata" / "NUTEV_RECOMMENDATION_CANDIDATES.csv")
    run_summary_path = project_root / "07_logs" / "run_summary.json"
    run_summary = {}
    if run_summary_path.exists():
        run_summary = json.loads(run_summary_path.read_text(encoding="utf-8"))

    total = int(run_summary.get("records", len(m)))
    captured = int(run_summary.get("downloads_ok", (m.get("download_status", pd.Series(dtype=str)).astype(str)=="pdf").sum() if not m.empty else 0))
    metadata_only = int(run_summary.get("downloads_failed", (m.get("download_status", pd.Series(dtype=str)).astype(str)=="metadata_only").sum() if not m.empty else 0))
    claims_total = int(run_summary.get("evidence_claims_total", len(c)))
    claims_supported = int(run_summary.get("evidence_claims_supported", (c.get("claim_status", pd.Series(dtype=str)).astype(str)=="supported").sum() if not c.empty else 0))
    claims_review = int(run_summary.get("evidence_claims_needs_review", (c.get("needs_human_review", pd.Series(dtype=bool)).astype(bool).sum()) if not c.empty else 0))
    rec_total = int(run_summary.get("recommendation_candidates_total", len(r)))
    rec_insuf = int(run_summary.get("recommendation_candidates_insufficient_evidence", (r.get("recommendation_status", pd.Series(dtype=str)).astype(str)=="insufficient_evidence").sum() if not r.empty else 0))
    conflicts = int(run_summary.get("conflicting_evidence_total", (c.get("claim_status", pd.Series(dtype=str)).astype(str)=="conflicting").sum() if not c.empty else 0))

    top_domains = c.get("nutev_domains", pd.Series(dtype=str)).astype(str).value_counts().head(5).to_dict() if not c.empty else {}
    top_lenses = c.get("evidence_lenses", pd.Series(dtype=str)).astype(str).value_counts().head(5).to_dict() if not c.empty else {}
    top_conditions = c.get("clinical_conditions", pd.Series(dtype=str)).astype(str).value_counts().head(5).to_dict() if not c.empty else {}

    out_dir = project_root / "08_docs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "NUTEV_PILOT_REPORT.md"
    out_path.write_text(
        "\n".join([
            "# NUTEV PILOT REPORT",
            f"- total de registros: {total}",
            f"- documentos capturados: {captured}",
            f"- metadata_only: {metadata_only}",
            f"- claims totais: {claims_total}",
            f"- claims suportados: {claims_supported}",
            f"- claims que precisam de revisão: {claims_review}",
            f"- recomendações candidatas: {rec_total}",
            f"- recomendações com evidência insuficiente: {rec_insuf}",
            f"- conflitos: {conflicts}",
            f"- top domínios NutEV: {top_domains}",
            f"- top lenses: {top_lenses}",
            f"- top conditions: {top_conditions}",
            "- lacunas: revisar claims inference_only/insufficient_evidence e recomendações draft_needs_evidence.",
            "- arquivos gerados: 02_metadata/*, 06_tables/*, 07_logs/run_summary.json, 08_docs/NUTEV_PILOT_REPORT.md",
            "- próximos passos de curadoria: dupla revisão humana + resolução de conflitos + refinamento do protocolo.",
        ]),
        encoding="utf-8",
    )
    return out_path
