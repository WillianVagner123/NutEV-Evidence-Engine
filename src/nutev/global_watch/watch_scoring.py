def score_watch_item(item):
    t=(item.get('title') or '').lower(); s=float(item.get('relevance_score') or 0)
    if 'guideline' in t: s+=40
    elif 'consensus' in t or 'scientific statement' in t: s+=30
    elif 'systematic review' in t or 'meta-analysis' in t: s+=20
    elif 'trial' in t: s+=15
    if any(p in t for p in ['editorial','commentary','letter','case report','animal','in vitro','login','buy','mostdownload']): s-=30
    if item.get('is_new'): s+=10
    return s
