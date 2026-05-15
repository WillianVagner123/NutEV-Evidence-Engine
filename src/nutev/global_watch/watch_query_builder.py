from pathlib import Path

from nutev.engine.ids import make_document_id
from nutev.querypacks.smart_builders import build_smart_queries, load_keyword_taxonomy


def build_watch_queries(categories, since_days, mode):
    taxonomy_path = Path('config/keyword_taxonomy.json')
    if taxonomy_path.exists():
        taxonomy = load_keyword_taxonomy(taxonomy_path)
        smart = build_smart_queries(taxonomy, ["busca1", "busca2a", "busca2b", "a3"], mode)
        out = []
        for ws, entries in smart.items():
            for e in entries:
                intent = e['intent']
                provider_hint = 'pubmed' if intent in {'guideline','review','trial','update'} else 'openalex'
                priority = 1 if intent in {'guideline','update'} else 2
                out.append({
                    "query_id": make_document_id({"title": e['query'], "provider": 'watch', "year": since_days}),
                    "category": categories[0] if categories else intent,
                    "intent": intent,
                    "query": e['query'],
                    "provider_hint": provider_hint,
                    "priority": priority,
                    "since_days": since_days,
                    "workstream_affinity": [ws],
                })
        return out
    return []
