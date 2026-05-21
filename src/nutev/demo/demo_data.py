from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def generate_demo_data(project_root: Path) -> None:
    dirs = ["02_metadata", "06_tables", "07_logs", "08_docs"]
    for d in dirs:
        (project_root / d).mkdir(parents=True, exist_ok=True)

    metadata = pd.DataFrame([
        {"document_id":"demo_1","title":"DEMO Guia alimentar oficial: in natura e ultraprocessados","source_provider":"official_web","year":2024,"country":"BR","download_status":"pdf","extraction_status":"ok","is_demo_data":True},
        {"document_id":"demo_2","title":"DEMO Diretriz clínica diabetes tipo 2 e padrão alimentar","source_provider":"pubmed","year":2023,"country":"US","download_status":"pdf","extraction_status":"ok","is_demo_data":True},
        {"document_id":"demo_3","title":"DEMO Diretriz hipertensão DASH sódio potássio","source_provider":"pubmed","year":2022,"country":"UK","download_status":"pdf","extraction_status":"ok","is_demo_data":True},
        {"document_id":"demo_4","title":"DEMO Revisão sistemática dieta mediterrânea e desfechos cardiometabólicos","source_provider":"europepmc","year":2021,"country":"ES","download_status":"pdf","extraction_status":"ok","is_demo_data":True},
        {"document_id":"demo_5","title":"DEMO Intervenção food literacy culinary skills adherence","source_provider":"openalex","year":2020,"country":"CA","download_status":"metadata_only","extraction_status":"missing","is_demo_data":True},
    ])
    claims = pd.DataFrame([
        {"claim_id":"c1","document_id":"demo_1","title":"DEMO Guia","claim_text":"Adults should reduce ultra-processed foods.","exact_quote":"Adults should reduce ultra-processed foods.","quote_location":"extracted_text","evidence_type":"official_guideline","claim_status":"supported","human_validation_status":"not_reviewed","needs_human_review":False,"evidence_quality_tier":"normative_high","evidence_quality_note":"Official guideline.","is_demo_data":True},
        {"claim_id":"c2","document_id":"demo_5","title":"DEMO Intervenção","claim_text":"Programs encourage culinary skills.","exact_quote":"","quote_location":"","evidence_type":"computational_inference","claim_status":"inference_only","human_validation_status":"not_reviewed","needs_human_review":True,"evidence_quality_tier":"inference_only","evidence_quality_note":"Inference only.","is_demo_data":True},
    ])
    recs = pd.DataFrame([
        {"recommendation_id":"r1","recommendation_text":"Priorizar alimentos in natura e reduzir ultraprocessados.","protocol_component":"diretrizes_dieteticas","supporting_claim_ids":"['c1']","supporting_document_ids":"['demo_1']","conflicting_claim_ids":"[]","recommendation_status":"ready_for_human_review","human_approval_status":"not_reviewed","is_demo_data":True},
        {"recommendation_id":"r2","recommendation_text":"Expandir oficinas culinárias.","protocol_component":"adesao_implementacao","supporting_claim_ids":"[]","supporting_document_ids":"[]","conflicting_claim_ids":"[]","recommendation_status":"draft_needs_evidence","human_approval_status":"not_reviewed","evidence_gap":"No supporting claims linked.","is_demo_data":True},
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
        "NUTEV_HUMAN_REVIEW_QUEUE.xlsx": claims[claims["needs_human_review"]==True],
    }.items():
        try: df.to_excel(project_root/"06_tables"/name, index=False)
        except Exception: df.to_csv((project_root/"06_tables"/name).with_suffix('.csv'), index=False)

    summary = {
        "records": 5, "downloads_ok": 4, "downloads_failed": 1, "ocr_docs": 4,
        "evidence_claims_total": 2, "evidence_claims_supported": 1, "evidence_claims_needs_review": 1,
        "recommendation_candidates_total": 2, "recommendation_candidates_ready_review": 1,
        "conflicting_evidence_total": 0, "human_review_decisions_total": 0,
    }
    (project_root/"07_logs"/"run_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    (project_root/"07_logs"/"run_events.jsonl").write_text('{"event_type":"created","message":"demo"}\n', encoding='utf-8')
    (project_root/"08_docs"/"NUTEV_METHODS_MASTER.md").write_text('# DEMO METHODS\nDados simulados apenas para demonstração.', encoding='utf-8')
