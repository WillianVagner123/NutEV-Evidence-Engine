from datetime import datetime, timezone
import os
from nutev.engine.events import emit_event, write_event
from nutev.engine.ids import make_document_id, make_run_id
from nutev.engine.job import create_search_case, create_search_job, write_search_case, write_search_job_snapshot
from nutev.global_watch.watch_diff import load_seen_items, mark_new_items, save_seen_items, update_seen_items
from nutev.global_watch.watch_digest import write_digest
from nutev.global_watch.watch_export import export_watch_outputs
from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item

def run_global_watch(settings, logger, since_days, mode, resume, official_crawl, country_discovery, llm_enabled):
    run_id=make_run_id(); logs=settings.output_dirs['07_logs']
    case=create_search_case('NutMEV Global Watch',['global_watch'],'watch',['pubmed','europepmc','openalex','crossref'],since_days=since_days,official_crawl=official_crawl,country_discovery=country_discovery,web_enabled=settings.web_enabled,llm_enabled=llm_enabled)
    job=create_search_job(case.case_id,run_id,[]); write_search_case(case,logs/'search_case.json'); write_event(emit_event(run_id,'global_watch_started','Global watch started'),logs/'run_events.jsonl')
    if llm_enabled and not os.getenv('OPENAI_API_KEY'): write_event(emit_event(run_id,'llm_disabled','OPENAI_API_KEY not found',event_kind='warning'),logs/'run_events.jsonl')
    rows=[]
    for q in build_watch_queries([],since_days,mode)[:20 if mode=='quick' else 40]:
        item={'title':f"{q['category']} update {q['query'][:40]}",'url':f"https://example.org/{q['query_id']}",'source_provider':'watch_seed','category':q['category'],'evidence_type':'guideline' if 'guideline' in q['query'].lower() else 'study','download_status':'metadata_only','failure_reason':'provider_disabled'}
        item['document_id']=make_document_id(item); item['relevance_score']=50; rows.append(item)
    state=settings.project_root/'09_global_watch'/'watch_state'/'seen_items.json'; seen=load_seen_items(state) if resume else {}
    rows=mark_new_items(rows,seen)
    for r in rows: r['novelty_score']=1.0 if r.get('is_new') else 0.2; r['watch_score']=score_watch_item(r)
    rows.sort(key=lambda x:x.get('watch_score',0),reverse=True); save_seen_items(state,update_seen_items(rows,seen))
    run_dir=settings.project_root/'09_global_watch'/'runs'/datetime.now(timezone.utc).date().isoformat(); new=[r for r in rows if r.get('is_new')]
    export_watch_outputs(rows,new,settings.project_root/'09_global_watch',run_dir); write_digest(rows,run_dir,settings.output_dirs['08_docs']/'NUTEV_GLOBAL_WATCH_LATEST.md')
    job.status='completed'; job.finished_at=datetime.now(timezone.utc); write_search_job_snapshot(job,logs/'search_job_snapshot.json',{'mode':mode,'since_days':since_days,'resume':resume}); write_event(emit_event(run_id,'global_watch_completed','Global watch completed'),logs/'run_events.jsonl')
    return {'rows':len(rows),'new_items':len(new)}
