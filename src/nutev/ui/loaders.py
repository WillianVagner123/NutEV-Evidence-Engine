from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from nutev.review.human_review import load_human_review_decisions, merge_human_review_decisions

def empty_with_warning(warning: str = 'not available yet'):
    return pd.DataFrame(), warning

def load_csv(path: Path):
    if not path.exists(): return empty_with_warning()
    try: return pd.read_csv(path), 'ok'
    except Exception as e: return empty_with_warning(f'not available yet: {e}')

def load_xlsx_or_csv(xlsx_path: Path, csv_path: Path | None = None):
    if xlsx_path.exists():
        try: return pd.read_excel(xlsx_path), 'ok'
        except Exception: pass
    if csv_path and csv_path.exists(): return load_csv(csv_path)
    return empty_with_warning()

def load_json_file(path: Path):
    if not path.exists(): return {}, 'not available yet'
    try: return json.loads(path.read_text(encoding='utf-8')), 'ok'
    except Exception as e: return {}, f'not available yet: {e}'

def load_jsonl(path: Path):
    if not path.exists(): return empty_with_warning()
    rows=[]
    try:
        for line in path.read_text(encoding='utf-8').splitlines():
            if line.strip(): rows.append(json.loads(line))
        return pd.DataFrame(rows), 'ok'
    except Exception as e:
        return empty_with_warning(f'not available yet: {e}')

def calculate_overview_metrics(run_summary: dict, metadata: pd.DataFrame, claims: pd.DataFrame, recs: pd.DataFrame) -> dict[str,int]:
    if run_summary:
        return {
            'total_records': int(run_summary.get('total_records', run_summary.get('records',0)) or 0),
            'downloaded_documents': int(run_summary.get('downloaded_documents', run_summary.get('downloads_ok',0)) or 0),
            'metadata_only_records': int(run_summary.get('metadata_only_records', run_summary.get('downloads_failed',0)) or 0),
            'extracted_texts': int(run_summary.get('extracted_texts', run_summary.get('ocr_docs',0)) or 0),
            'evidence_claims_total': int(run_summary.get('evidence_claims_total',0) or 0),
            'evidence_claims_supported': int(run_summary.get('evidence_claims_supported',0) or 0),
            'evidence_claims_needs_review': int(run_summary.get('evidence_claims_needs_review',0) or 0),
            'recommendation_candidates_total': int(run_summary.get('recommendation_candidates_total',0) or 0),
            'recommendation_candidates_ready_review': int(run_summary.get('recommendation_candidates_ready_review',0) or 0),
            'recommendation_candidates_insufficient_evidence': int(run_summary.get('recommendation_candidates_insufficient_evidence',0) or 0),
            'conflicting_evidence_total': int(run_summary.get('conflicting_evidence_total',0) or 0),
            'human_review_decisions_total': int(run_summary.get('human_review_decisions_total',0) or 0),
        }
    return {
        'total_records': int(len(metadata)),
        'downloaded_documents': int((metadata.get('download_status', pd.Series(dtype=str)).astype(str)=='pdf').sum()) if not metadata.empty else 0,
        'metadata_only_records': int((metadata.get('download_status', pd.Series(dtype=str)).astype(str)=='metadata_only').sum()) if not metadata.empty else 0,
        'extracted_texts': int((metadata.get('extraction_status', pd.Series(dtype=str)).astype(str)=='ok').sum()) if not metadata.empty else 0,
        'evidence_claims_total': int(len(claims)),
        'evidence_claims_supported': int((claims.get('claim_status', pd.Series(dtype=str)).astype(str)=='supported').sum()) if not claims.empty else 0,
        'evidence_claims_needs_review': int((claims.get('needs_human_review', pd.Series(dtype=bool)).astype(bool)).sum()) if not claims.empty else 0,
        'recommendation_candidates_total': int(len(recs)),
        'recommendation_candidates_ready_review': int((recs.get('recommendation_status', pd.Series(dtype=str)).astype(str)=='ready_for_human_review').sum()) if not recs.empty else 0,
        'recommendation_candidates_insufficient_evidence': int((recs.get('recommendation_status', pd.Series(dtype=str)).astype(str)=='insufficient_evidence').sum()) if not recs.empty else 0,
        'conflicting_evidence_total': int((claims.get('claim_status', pd.Series(dtype=str)).astype(str)=='conflicting').sum()) if not claims.empty else 0,
        'human_review_decisions_total': 0,
    }


def load_and_merge_human_review_queue(project_root: Path, queue_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    decisions_df = load_human_review_decisions(project_root)
    return merge_human_review_decisions(queue_df, decisions_df), decisions_df
