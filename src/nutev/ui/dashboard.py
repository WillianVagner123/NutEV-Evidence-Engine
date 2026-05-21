from __future__ import annotations

from pathlib import Path
import json
import os
import subprocess

import pandas as pd
import streamlit as st

from nutev.ui.loaders import calculate_overview_metrics, load_and_merge_human_review_queue, load_csv, load_json_file, load_jsonl, load_xlsx_or_csv
from nutev.review.human_review import append_human_review_decision
from nutev.provider_settings import load_provider_registry, load_provider_settings, save_provider_settings


def _load_governance_rules() -> dict:
    p = Path('config') / 'llm_governance_rules.json'
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _run_nutev_command(cmd: list[str]) -> tuple[bool, str]:
    try:
        completed = subprocess.run(cmd, check=False, text=True, capture_output=True)
        output = (completed.stdout or '') + ('\n' + completed.stderr if completed.stderr else '')
        return completed.returncode == 0, output.strip()
    except Exception as exc:
        return False, str(exc)


def run_dashboard(project_root: Path) -> None:
    st.set_page_config(page_title='NutEV Control Center', layout='wide')
    st.title('NutEV Control Center')
    st.warning('Este painel é uma ferramenta de auditoria e monitoramento. Ele não substitui triagem, interpretação e validação humana.')
    st.warning('A aprovação final depende de revisão humana explícita e vínculo documental.')

    metadata, _ = load_csv(project_root / '02_metadata' / 'metadata_master.csv')
    claims, _ = load_csv(project_root / '02_metadata' / 'NUTEV_EVIDENCE_CLAIMS.csv')
    recs, _ = load_csv(project_root / '02_metadata' / 'NUTEV_RECOMMENDATION_CANDIDATES.csv')
    global_matrix, gm_status = load_xlsx_or_csv(project_root / '06_tables' / 'NUTEV_GLOBAL_EVIDENCE_MATRIX.xlsx', project_root / '06_tables' / 'NUTEV_GLOBAL_EVIDENCE_MATRIX.csv')
    hrq, _ = load_xlsx_or_csv(project_root / '06_tables' / 'NUTEV_HUMAN_REVIEW_QUEUE.xlsx', project_root / '06_tables' / 'NUTEV_HUMAN_REVIEW_QUEUE.csv')
    run_summary, _ = load_json_file(project_root / '07_logs' / 'run_summary.json')
    events, _ = load_jsonl(project_root / '07_logs' / 'run_events.jsonl')
    methods_path = project_root / '08_docs' / 'NUTEV_METHODS_MASTER.md'

    pages = [
        'Overview', 'Pipeline Status', 'Global Evidence Matrix', 'Audit Engine', 'Recommendation Candidates',
        'Human Review Queue', 'Logs & Run Summary', 'Methods Preview', 'Provider Settings + LLM Governance',
        'Run Control', 'Export Center', 'Pilot Manager', 'Protocol Builder', 'Evidence Quality Board',
        'Human Review Workspace', 'Source Registry Manager', 'Search Strategy Builder', 'Cost & Usage Monitor',
        'Qualification Report Generator'
    ]
    page = st.sidebar.radio('Pages', pages)

    if page == 'Overview':
        m = calculate_overview_metrics(run_summary, metadata, claims, recs)
        cols = st.columns(4)
        for i, (k, v) in enumerate(m.items()):
            cols[i % 4].metric(k, v)

    elif page == 'Provider Settings + LLM Governance':
        st.subheader('Provider Settings')
        reg = load_provider_registry(Path('config')).get('providers', [])
        settings = load_provider_settings(project_root).get('providers', {})
        for p in reg:
            pid = p['provider_id']
            cfg = settings.get(pid, {})
            st.write({'provider_id': pid, 'type': p.get('provider_type'), 'enabled': cfg.get('enabled', False), 'mode': cfg.get('mode', 'disabled')})
        with st.form('provider_settings_form'):
            pid = st.selectbox('provider_id', [p['provider_id'] for p in reg])
            enabled = st.checkbox('enabled', value=settings.get(pid, {}).get('enabled', False))
            mode = st.text_input('mode', value=settings.get(pid, {}).get('mode', 'assistive'))
            model = st.text_input('model', value=settings.get(pid, {}).get('model', ''))
            base_url = st.text_input('base_url', value=settings.get(pid, {}).get('base_url', ''))
            env_var = st.text_input('env_var', value=settings.get(pid, {}).get('env_var', ''))
            secret_source = st.selectbox('secret_source', ['env', 'local'])
            api_key = st.text_input('api_key (opcional, local)', type='password')
            local_only = st.checkbox('local_only', value=True)
            if st.form_submit_button('Salvar provider'):
                all_settings = load_provider_settings(project_root)
                all_settings.setdefault('providers', {})
                item = {'enabled': enabled, 'mode': mode, 'model': model, 'base_url': base_url, 'env_var': env_var, 'secret_source': secret_source, 'local_only': local_only}
                if api_key:
                    item['api_key'] = api_key
                all_settings['providers'][pid] = item
                save_provider_settings(project_root, all_settings)
                st.success('Configuração salva.')

        st.subheader('LLM Governance')
        governance = _load_governance_rules()
        st.json(governance if governance else {'status': 'rules file not available'})

    elif page == 'Run Control':
        st.subheader('Run Control')
        st.caption('Inicie fluxos principais direto do Control Center.')
        c1, c2, c3 = st.columns(3)
        if c1.button('Run Demo Data'):
            ok, out = _run_nutev_command(['python', '-m', 'nutev.cli', 'demo-data', '--project-root', str(project_root)])
            (st.success if ok else st.error)(out or 'done')
        if c2.button('Run Pipeline'):
            ok, out = _run_nutev_command(['python', '-m', 'nutev.cli', 'run', '--project-root', str(project_root)])
            (st.success if ok else st.error)(out or 'done')
        if c3.button('Run Pilot Report'):
            ok, out = _run_nutev_command(['python', '-m', 'nutev.cli', 'pilot-report', '--project-root', str(project_root)])
            (st.success if ok else st.error)(out or 'done')

    elif page == 'Export Center':
        st.subheader('Export Center')
        exports = [
            project_root / '06_tables' / 'NUTEV_GLOBAL_EVIDENCE_MATRIX.csv',
            project_root / '06_tables' / 'NUTEV_PROTOCOL_TRANSLATION_MATRIX.csv',
            project_root / '08_docs' / 'NUTEV_METHODS_MASTER.md',
            project_root / '08_docs' / 'NUTEV_PILOT_REPORT.md',
        ]
        for p in exports:
            if p.exists():
                st.download_button(f'Download {p.name}', p.read_bytes(), file_name=p.name)
            else:
                st.info(f'Not generated yet: {p.name}')

    elif page == 'Pilot Manager':
        st.subheader('Pilot Manager')
        st.write({'recommended_documents_min': 20, 'recommended_documents_max': 30})
        st.write({'current_metadata_records': len(metadata)})

    elif page == 'Protocol Builder':
        st.subheader('Protocol Builder')
        approved = recs[recs.get('human_approval_status', pd.Series(dtype=str)).astype(str).isin(['approved', 'revised'])] if not recs.empty else pd.DataFrame()
        st.dataframe(approved if not approved.empty else pd.DataFrame({'status': ['no approved recommendations yet']}), use_container_width=True)

    elif page == 'Evidence Quality Board':
        st.subheader('Evidence Quality Board')
        if claims.empty:
            st.info('Claims not available yet.')
        else:
            by_status = claims.get('claim_status', pd.Series(dtype=str)).value_counts().rename_axis('claim_status').reset_index(name='count')
            st.dataframe(by_status, use_container_width=True)

    elif page == 'Human Review Workspace':
        st.subheader('Human Review Workspace')
        q, decisions_df = load_and_merge_human_review_queue(project_root, hrq.copy())
        st.dataframe(q, use_container_width=True)
        st.dataframe(decisions_df, use_container_width=True)

    elif page == 'Source Registry Manager':
        st.subheader('Source Registry Manager')
        src_registry = load_json_file(Path('config') / 'source_registry.json')[0]
        st.json(src_registry if src_registry else {'status': 'not available'})

    elif page == 'Search Strategy Builder':
        st.subheader('Search Strategy Builder')
        st.info('Use este espaço para revisar querypacks por base antes do run.')
        querypack = st.text_area('querypack_draft', value='("condition") AND (guideline OR consensus)')
        st.code(querypack)

    elif page == 'Cost & Usage Monitor':
        st.subheader('Cost & Usage Monitor')
        if events.empty:
            st.info('run_events.jsonl ainda não disponível.')
        else:
            token_cols = [c for c in ['prompt_tokens', 'completion_tokens', 'total_tokens', 'estimated_cost_usd'] if c in events.columns]
            st.dataframe(events[token_cols].tail(200) if token_cols else pd.DataFrame({'status': ['no usage columns in logs']}), use_container_width=True)

    elif page == 'Qualification Report Generator':
        st.subheader('Qualification Report Generator')
        st.caption('Gera texto metodológico consolidado para colar na qualificação.')
        if st.button('Generate Pilot Report'):
            ok, out = _run_nutev_command(['python', '-m', 'nutev.cli', 'pilot-report', '--project-root', str(project_root)])
            (st.success if ok else st.error)(out or 'done')

    elif page == 'Pipeline Status':
        stages = ['Discovery', 'Capture', 'Extraction', 'Classification', 'Claim Extraction', 'Claim Evaluation', 'Recommendation Generation', 'Human Review', 'Protocol Translation']
        for s in stages:
            st.subheader(s)
            st.write({'status': 'not available yet' if events.empty else 'available', 'total_records': len(metadata)})

    elif page == 'Global Evidence Matrix':
        st.dataframe(global_matrix if not global_matrix.empty else pd.DataFrame({'status': [gm_status]}), use_container_width=True)

    elif page == 'Audit Engine':
        st.dataframe(claims if not claims.empty else pd.DataFrame({'status': ['not available yet']}), use_container_width=True)

    elif page == 'Recommendation Candidates':
        st.dataframe(recs if not recs.empty else pd.DataFrame({'status': ['not available yet']}), use_container_width=True)

    elif page == 'Human Review Queue':
        q, decisions_df = load_and_merge_human_review_queue(project_root, hrq.copy())
        st.dataframe(q, use_container_width=True)
        st.dataframe(decisions_df, use_container_width=True)
        with st.form('human_review_form'):
            item_type = st.selectbox('item_type', ['claim', 'recommendation_candidate', 'conflict'])
            item_id = st.text_input('item_id')
            reviewer_name = st.text_input('reviewer_name')
            reviewer_role = st.selectbox('reviewer_role', ['reviewer_1', 'reviewer_2'])
            reviewer_decision = st.selectbox('reviewer_decision', ['approve', 'reject', 'needs_more_evidence', 'needs_second_reviewer'])
            reviewer_notes = st.text_area('reviewer_notes')
            final_decision = st.selectbox('final_decision', ['pending', 'approved', 'rejected'])
            if st.form_submit_button('Registrar decisão'):
                append_human_review_decision(project_root, {'item_type': item_type, 'item_id': item_id, 'reviewer_name': reviewer_name, 'reviewer_role': reviewer_role, 'reviewer_decision': reviewer_decision, 'reviewer_notes': reviewer_notes, 'final_decision': final_decision})
                st.success('Decisão registrada.')

    elif page == 'Logs & Run Summary':
        st.json(run_summary if run_summary else {'status': 'not available yet'})
        st.dataframe(events.tail(200) if not events.empty else pd.DataFrame({'status': ['not available yet']}), use_container_width=True)

    elif page == 'Methods Preview':
        if methods_path.exists():
            st.markdown(methods_path.read_text(encoding='utf-8'))
        else:
            st.info('Methods document not generated yet.')


def main() -> None:
    default_root = os.environ.get('NUTEV_DASHBOARD_PROJECT_ROOT', './project_output')
    root = Path(st.sidebar.text_input('Project Root', default_root))
    run_dashboard(root)


if __name__ == '__main__':
    main()
