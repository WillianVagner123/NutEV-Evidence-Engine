import json
from datetime import datetime, timezone

def load_seen_items(path):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
def save_seen_items(path, items):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
def mark_new_items(candidates, seen_items):
    for c in candidates: c['is_new']=c.get('document_id') not in seen_items
    return candidates
def update_seen_items(candidates, seen_items):
    now=datetime.now(timezone.utc).date().isoformat(); out=dict(seen_items)
    for c in candidates:
        did=c.get('document_id');
        if not did: continue
        prev=out.get(did,{})
        out[did]={"document_id":did,"first_seen_date":prev.get('first_seen_date',now),"last_seen_date":now,"title":c.get('title',''),"doi":c.get('doi',''),"url":c.get('url',''),"source_provider":c.get('source_provider',''),"category":c.get('category',''),"relevance_score":c.get('relevance_score',0),"last_status":c.get('download_status','metadata_only')}
    return out
