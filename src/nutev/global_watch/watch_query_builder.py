from nutev.engine.ids import make_document_id
from nutev.global_watch.watch_config import MODE_LIMITS, WATCH_CATEGORIES

def build_watch_queries(categories, since_days, mode):
    selected=categories or list(WATCH_CATEGORIES.keys()); limit=MODE_LIMITS.get(mode,6); out=[]
    for cat in selected:
        for term in WATCH_CATEGORIES.get(cat,[])[:limit]:
            q=f'({term}) AND (nutrition OR diet OR obesity OR cardiometabolic)'
            out.append({"query_id":make_document_id({"title":q,"provider":"watch","year":since_days}),"category":cat,"query":q,"provider_hint":"pubmed","priority":1 if any(x in term.lower() for x in ["guideline","consensus"]) else 2,"since_days":since_days})
    return out
