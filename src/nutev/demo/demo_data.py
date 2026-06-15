from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from nutev.audit.evidence_convergence import export_evidence_convergence_matrix
from nutev.audit.gap_register import export_evidence_gap_register
from nutev.export.excel_writer import write_excel_file
from nutev.export.scientific_rigor_report import write_originality_matrix, write_scientific_rigor_report
from nutev.protocol.locked_items import export_locked_protocol_items
from nutev.protocol.readiness import build_protocol_readiness_matrix, export_protocol_readiness_matrix


def generate_demo_data(project_root: Path) -> None:
    dirs = ["02_metadata", "06_tables", "07_logs", "08_docs"]
    for d in dirs:
        (project_root / d).mkdir(parents=True, exist_ok=True)

    metadata = pd.DataFrame([
        {"document_id":"demo_1","title":"DEMO Guia alimentar oficial: in natura e ultraprocessados","source_provider":"official_web","year":2024,"country":"BR","download_status":"pdf","extraction_status":"ok","is_demo_data":True,"evidence_lenses":"official_guidelines"},
        {"document_id":"demo_2","title":"DEMO Diretriz clínica diabetes tipo 2 e padrão alimentar","source_provider":"pubmed","year":2023,"country":"US","download_status":"pdf","extraction_status":"ok","is_demo_data":True,"evidence_lenses":"clinical_guidelines"},
        {"document_id":"demo_3","title":"DEMO Diretriz hipertensão DASH sódio potássio","source_provider":"pubmed","year":2022,"country":"UK","download_status":"pdf","extraction_status":"ok","is_demo_data":True,"evidence_lenses":"clinical_guidelines"},
        {"document_id":"demo_4","title":"DEMO Revisão sistemática dieta mediterrânea e desfechos cardiometabólicos","source_provider":"europepmc","year":2021,"country":"ES","download_status":"pdf","extraction_status":"ok","is_demo_data":True,"evidence_lenses":"systematic_reviews"},
        {"document_id":"demo_5","title":"DEMO Intervenção food literacy culinary skills adherence","source_provider":"openalex","year":2020,"country":"CA","download_status":"metadata_only","extraction_status":"missing","is_demo_data":True,"evidence_lenses":"implementation"},
    ])
    claims = pd.DataFrame([
        {"claim_id":"c1","document_id":"demo_1","title":"DEMO Guia","claim_text":"Adults should reduce ultra-processed foods.","exact_quote":"Adults should reduce ultra-processed foods.","quote_location":"extracted_text","evidence_type":"official_guideline","claim_status":"supported","human_validation_status":"not_reviewed","needs_human_review":False,"evidence_quality_tier":"normative_high","evidence_quality_note":"Official guideline.","nutev_domains":"food_processing","evidence_lenses":"official_guidelines","protocol_components":"diretrizes_dieteticas","is_demo_data":True},
        {"claim_id":"c2","document_id":"demo_4","title":"DEMO Revisão","claim_text":"Mediterranean dietary patterns improve cardiometabolic outcomes.","exact_quote":"Mediterranean dietary patterns improve cardiometabolic outcomes.","quote_location":"abstract","evidence_type":"systematic_review","claim_status":"supported","human_validation_status":"not_reviewed","needs_human_review":False,"evidence_quality_tier":"research_high","evidence_quality_note":"Systematic review.","nutev_domains":"dietary_pattern","evidence_lenses":"systematic_reviews","protocol_components":"diretrizes_dieteticas","is_demo_data":True},
        {"claim_id":"c3","document_id":"demo_5","title":"DEMO Intervenção","claim_text":"Programs encourage culinary skills.","exact_quote":"","quote_location":"","evidence_type":"computational_inference","claim_status":"inference_only","human_validation_status":"not_reviewed","needs_human_review":True,"evidence_quality_tier":"inference_only","evidence_quality_note":"Inference only.","nutev_domains":"culinary_skills","evidence_lenses":"implementation","protocol_components":"adesao_implementacao","is_demo_data":True},
    ])
    recs = pd.DataFrame([
        {"recommendation_id":"r1","recommendation_text":"Priorizar alimentos in natura e reduzir ultraprocessados.","protocol_component":"diretrizes_dieteticas","nutev_domains":"food_processing","supporting_claim_ids":"['c1']","supporting_document_ids":"['demo_1']","conflicting_claim_ids":"[]","evidence_lenses":"official_guidelines","recommendation_status":"ready_for_human_review","human_approval_status":"not_reviewed","is_demo_data":True},
        {"recommendation_id":"r2","recommendation_text":"Incorporar padrão mediterrâneo quando aplicável ao risco cardiometabólico.","protocol_component":"diretrizes_dieteticas","nutev_domains":"dietary_pattern","supporting_claim_ids":"['c2']","supporting_document_ids":"['demo_4']","conflicting_claim_ids":"[]","evidence_lenses":"systematic_reviews","recommendation_status":"ready_for_human_review","human_approval_status":"approved","is_demo_data":True},
        {"recommendation_id":"r3","recommendation_text":"Expandir oficinas culinárias.","protocol_component":"adesao_implementacao","nutev_domains":"culinary_skills","supporting_claim_ids":"[]","supporting_document_ids":"[]","conflicting_claim_ids":"[]","evidence_lenses":"implementation","recommendation_status":"draft_needs_evidence","human_approval_status":"not_reviewed","evidence_gap":"No supporting claims linked.","is_demo_data":True},
    ])
    audit = pd.DataFrame([{"audit_event_id":"a1","run_id":"demo_run","event_stage":"claim_evaluation","event_type":"created","event_message":"demo","is_demo_data":True}])

    metadata.to_csv(project_root/"02_metadata"/"metadata_master.csv", index=False)
    claims.to_csv(project_root/"02_metadata"/"NUTEV_EVIDENCE_CLAIMS.csv", index=False)
    recs.to_csv(project_root/"02_metadata"/"NUTEV_RECOMMENDATION_CANDIDATES.csv", index=False)
    audit.to_csv(project_root/"02_metadata"/"NUTEV_RECOMMENDATION_AUDIT_TRAIL.csv", index=False)

    for name, df in {
        "NUTEV_GLOBAL_EVIDENCE_MATRIX.xlsx": metadata,
        "NUTEV_PROTOCOL_TRANSLATION_MATRIX.xlsx": metadata,
        "NUTEV_EVIDENCE_CLAIMS.xlsx": claims,
        "NUTEV_RECOMMENDATION_CANDIDATES.xlsx": recs,
        "NUTEV_HUMAN_REVIEW_QUEUE.xlsx": claims[claims["needs_human_review"].astype(bool)],
    }.items():
        try:
            df.to_excel(project_root/"06_tables"/name, index=False)
        except Exception:
            df.to_csv((project_root/"06_tables"/name).with_suffix('.csv'), index=False)

    claims_records = claims.to_dict("records")
    rec_records = recs.to_dict("records")
    convergence_summary = export_evidence_convergence_matrix(claims_records, rec_records, project_root / "06_tables")
    gaps_total = export_evidence_gap_register(claims_records, rec_records, [], project_root / "06_tables")
    protocol_ready_total = export_protocol_readiness_matrix(rec_records, claims_records, project_root / "06_tables")
    readiness_df = build_protocol_readiness_matrix(rec_records, claims_records)
    locked_total = export_locked_protocol_items(rec_records, readiness_df, project_root / "06_tables")
    write_originality_matrix(Path("config"), project_root / "06_tables")
    write_excel_file(pd.DataFrame([{"percent_agreement": 0, "kappa_not_computed_reason": "demo data has no paired reviewer decisions"}]), project_root / "06_tables" / "NUTEV_REVIEWER_AGREEMENT.xlsx")
    write_excel_file(pd.DataFrame(columns=["item_id", "reason", "adjudication_status"]), project_root / "06_tables" / "NUTEV_ADJUDICATION_QUEUE.xlsx")

    conceptual_path = Path("config") / "nutev_conceptual_model.json"
    conceptual_model = json.loads(conceptual_path.read_text(encoding="utf-8")) if conceptual_path.exists() else {}
    write_scientific_rigor_report(project_root / "08_docs", conceptual_model, claims_records, rec_records, [], convergence_summary, protocol_ready_total, gaps_total, locked_total)

    summary = {
        "records": 5, "downloads_ok": 4, "downloads_failed": 1, "ocr_docs": 4,
        "evidence_claims_total": 3, "evidence_claims_supported": 2, "evidence_claims_needs_review": 1,
        "recommendation_candidates_total": 3, "recommendation_candidates_ready_review": 2,
        "conflicting_evidence_total": 0, "human_review_decisions_total": 0,
        "evidence_convergence_total": sum(convergence_summary.values()),
        "protocol_ready_total": protocol_ready_total,
        "evidence_gaps_total": gaps_total,
        "adjudication_queue_total": 0,
        "locked_protocol_items_total": locked_total,
    }
    (project_root/"07_logs"/"run_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    (project_root/"07_logs"/"run_events.jsonl").write_text('{"event_type":"created","message":"demo"}\n', encoding='utf-8')
    (project_root/"08_docs"/"NUTEV_METHODS_MASTER.md").write_text('# DEMO METHODS\nDados simulados apenas para demonstracao. RecommendationCandidate nao e recomendacao final. Protocol ready depende de revisao humana, lastro documental e ausencia de conflito nao adjudicado.', encoding='utf-8')
