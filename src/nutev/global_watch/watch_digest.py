import json
from datetime import datetime, timezone

def write_digest(rows, run_dir, latest_doc_path):
    d=datetime.now(timezone.utc).date().isoformat(); run_dir.mkdir(parents=True, exist_ok=True)
    md=run_dir/'global_watch_digest.md'; js=run_dir/'global_watch_digest.json'; top=rows[:10]
    lines=[f'# NutMEV Global Watch — {d}','','## Resumo executivo',f'- total de itens encontrados: {len(rows)}',f"- novos itens: {sum(1 for r in rows if r.get('is_new'))}",'','## Top 10 para leitura imediata','| prioridade | título | tipo | fonte | país/região | por que importa | link | status |','|---|---|---|---|---|---|---|---|']
    for r in top: lines.append(f"| {r.get('watch_score',0):.1f} | {r.get('title','')} | {r.get('evidence_type','')} | {r.get('source_provider','')} | {r.get('region','')} | {r.get('why_it_matters','')} | {r.get('url','')} | {r.get('download_status','metadata_only')} |")
    md.write_text('\n'.join(lines),encoding='utf-8'); js.write_text(json.dumps({'date':d,'total':len(rows),'items':rows},ensure_ascii=False,indent=2),encoding='utf-8')
    latest_doc_path.parent.mkdir(parents=True, exist_ok=True); latest_doc_path.write_text(md.read_text(encoding='utf-8'),encoding='utf-8'); return md,js
