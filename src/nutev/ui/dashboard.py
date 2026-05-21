from __future__ import annotations

from pathlib import Path
import os

import pandas as pd
import streamlit as st

from nutev.ui.loaders import calculate_overview_metrics, load_and_merge_human_review_queue, load_csv, load_json_file, load_jsonl, load_xlsx_or_csv
from nutev.review.human_review import append_human_review_decision


def run_dashboard(project_root: Path) -> None:
    st.set_page_config(page_title='NutEV Control Center', layout='wide')
    st.title('NutEV Control Center')
    st.warning('Este painel é uma ferramenta de auditoria e monitoramento. Ele não substitui triagem, interpretação e validação humana.')
    st.warning('A aprovação final depende de revisão humana explícita e vínculo documental.')

    metadata, _ = load_csv(project_root / '02_metadata' / 'metadata_master.csv')
    claims, _ = load_csv(project_root / '02_metadata' / 'NUTEV_EVIDENCE_CLAIMS.csv')
    recs, _ = load_csv(project_root / '02_metadata' / 'NUTEV_RECOMMENDATION_CANDIDATES.csv')
    trail, _ = load_csv(project_root / '02_metadata' / 'NUTEV_RECOMMENDATION_AUDIT_TRAIL.csv')
    global_matrix, gm_status = load_xlsx_or_csv(project_root / '06_tables' / 'NUTEV_GLOBAL_EVIDENCE_MATRIX.xlsx', project_root / '06_tables' / 'NUTEV_GLOBAL_EVIDENCE_MATRIX.csv')
    protocol_matrix, pm_status = load_xlsx_or_csv(project_root / '06_tables' / 'NUTEV_PROTOCOL_TRANSLATION_MATRIX.xlsx', project_root / '06_tables' / 'NUTEV_PROTOCOL_TRANSLATION_MATRIX.csv')
    hrq, _ = load_xlsx_or_csv(project_root / '06_tables' / 'NUTEV_HUMAN_REVIEW_QUEUE.xlsx', project_root / '06_tables' / 'NUTEV_HUMAN_REVIEW_QUEUE.csv')
    run_summary, _ = load_json_file(project_root / '07_logs' / 'run_summary.json')
    events, _ = load_jsonl(project_root / '07_logs' / 'run_events.jsonl')
    methods_path = project_root / '08_docs' / 'NUTEV_METHODS_MASTER.md'

    page = st.sidebar.radio('Pages', ['Overview','Pipeline Status','Global Evidence Matrix','Audit Engine','Recommendation Candidates','Human Review Queue','Logs & Run Summary','Methods Preview'])

    if page == 'Overview':
        m = calculate_overview_metrics(run_summary, metadata, claims, recs)
        cols = st.columns(4)
        for i, (k, v) in enumerate(m.items()): cols[i % 4].metric(k, v)
        st.info('Nenhuma recomendação NutEV deve ser considerada final sem claims documentais e validação humana.')

    elif page == 'Pipeline Status':
        stages = ['Discovery','Capture','Extraction','Classification','Claim Extraction','Claim Evaluation','Recommendation Generation','Human Review','Protocol Translation']
        for s in stages:
            st.subheader(s)
            st.write({'status': 'not available yet' if events.empty else 'available', 'total_records': len(metadata), 'warnings': int((events.get('event_kind', pd.Series(dtype=str))=='warning').sum()) if not events.empty else 0})

    elif page == 'Global Evidence Matrix':
        if global_matrix.empty:
            st.warning(f'Global matrix {gm_status}')
        else:
            st.dataframe(global_matrix, use_container_width=True)

    elif page == 'Audit Engine':
        if claims.empty: st.warning('not available yet')
        else:
            st.dataframe(claims[[c for c in ['claim_id','document_id','title','claim_text','exact_quote','source_url','evidence_type','claim_status','human_validation_status','needs_human_review'] if c in claims.columns]], use_container_width=True)

    elif page == 'Recommendation Candidates':
        if recs.empty: st.warning('not available yet')
        else:
            view = recs[[c for c in ['recommendation_id','recommendation_text','protocol_component','supporting_claim_ids','supporting_document_ids','conflicting_claim_ids','recommendation_status','human_approval_status','evidence_gap'] if c in recs.columns]].copy()
            st.dataframe(view, use_container_width=True)
            if 'supporting_claim_ids' in recs.columns and (recs['supporting_claim_ids'].astype(str).str.strip().isin(['', '[]'])).any():
                st.error('Esta recomendação não pode avançar sem suporte documental.')

    elif page == 'Human Review Queue':
        q = hrq.copy()
        if not claims.empty:
            add = claims[(claims.get('needs_human_review', False)==True) | (claims.get('claim_status', pd.Series(dtype=str)).astype(str).isin(['inference_only','insufficient_evidence','conflicting']))]
            q = pd.concat([q, add], ignore_index=True) if not add.empty else q
        if not recs.empty:
            add_r = recs[recs.get('recommendation_status', pd.Series(dtype=str)).astype(str).isin(['insufficient_evidence','conflicting_evidence'])]
            q = pd.concat([q, add_r], ignore_index=True) if not add_r.empty else q
        q, decisions_df = load_and_merge_human_review_queue(project_root, q)
        if q.empty: st.warning('not available yet')
        else:
            st.dataframe(q, use_container_width=True)
            st.download_button('Download Human Review Queue CSV', q.to_csv(index=False).encode('utf-8'), file_name='NUTEV_HUMAN_REVIEW_QUEUE.csv')
            st.download_button('Download Human Review Template CSV', pd.DataFrame([{
                'item_type':'claim','item_id':'','reviewer_name':'','reviewer_role':'reviewer_1','reviewer_decision':'needs_more_evidence','reviewer_notes':'','final_decision':'pending'
            }]).to_csv(index=False).encode('utf-8'), file_name='human_review_template.csv')
            st.subheader('Decisões humanas registradas')
            st.dataframe(decisions_df, use_container_width=True)
            with st.form('human_review_form'):
                item_type = st.selectbox('item_type', ['claim','recommendation_candidate','conflict','metadata_only_record','unsupported_claim'])
                item_id = st.text_input('item_id')
                reviewer_name = st.text_input('reviewer_name')
                reviewer_role = st.selectbox('reviewer_role', ['principal_investigator','advisor','coadvisor','reviewer_1','reviewer_2','external_reviewer'])
                reviewer_decision = st.selectbox('reviewer_decision', ['approve','approve_with_revision','reject','needs_more_evidence','needs_second_reviewer','conflict','not_applicable'])
                reviewer_notes = st.text_area('reviewer_notes')
                final_decision = st.selectbox('final_decision', ['pending','approved','revised','rejected','insufficient_evidence','conflicting_evidence'])
                if st.form_submit_button('Registrar decisão'):
                    append_human_review_decision(project_root, {
                        'item_type': item_type, 'item_id': item_id, 'reviewer_name': reviewer_name,
                        'reviewer_role': reviewer_role, 'reviewer_decision': reviewer_decision,
                        'reviewer_notes': reviewer_notes, 'final_decision': final_decision
                    })
                    st.success('Decisão registrada.')

    elif page == 'Logs & Run Summary':
        st.subheader('run_summary.json')
        st.json(run_summary if run_summary else {'status':'not available yet'})
        st.subheader('run_events.jsonl')
        st.dataframe(events.tail(200) if not events.empty else pd.DataFrame({'status':['not available yet']}), use_container_width=True)
        failed, _ = load_csv(project_root / '03_corpus' / 'failed_downloads.csv')
        st.subheader('failed_downloads.csv')
        st.dataframe(failed if not failed.empty else pd.DataFrame({'status':['not available yet']}), use_container_width=True)

    elif page == 'Methods Preview':
        if methods_path.exists(): st.markdown(methods_path.read_text(encoding='utf-8'))
        else: st.info('Methods document not generated yet.')


def main() -> None:
    default_root = os.environ.get('NUTEV_DASHBOARD_PROJECT_ROOT', './project_output')
    root = Path(st.sidebar.text_input('Project Root', default_root))
    run_dashboard(root)

if __name__ == '__main__':
    main()
