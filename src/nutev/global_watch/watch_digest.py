import json
from datetime import datetime, timezone

CATS=["guidelines_consensus","lifestyle_medicine","obesity_cardiometabolic","diet_patterns","implementation_behavior","food_literacy_culinary_commensality","frameworks_instruments"]


def write_digest(rows, run_dir, latest_doc_path):
    d=datetime.now(timezone.utc).date().isoformat(); run_dir.mkdir(parents=True, exist_ok=True)
    md=run_dir/'global_watch_digest.md'; js=run_dir/'global_watch_digest.json'; top=rows[:10]
    cnt=lambda st: sum(1 for r in rows if r.get('download_status')==st)
    lines=[f'# NutMEV Global Watch — {d}','','## Resumo executivo',f'- total de itens: {len(rows)}',f"- novos itens: {sum(1 for r in rows if r.get('is_new'))}",f"- alta prioridade: {sum(1 for r in rows if (r.get('watch_score') or 0)>=80)}",f"- PDFs capturados: {cnt('pdf')}",f"- HTML snapshots: {cnt('html_snapshot')}",f"- metadata-only: {cnt('metadata_only')}",f"- falhas: {cnt('failed')}",'','## Top 10 para leitura imediata','| prioridade | título | tipo | provider | categoria | impacto provável | status | link |','|---|---|---|---|---|---|---|---|']
    for i,r in enumerate(top,1): lines.append(f"| {i} | {r.get('title','')} | {r.get('evidence_type','')} | {r.get('source_provider','')} | {r.get('category','')} | {r.get('why_it_matters','')} | {r.get('download_status','metadata_only')} | {r.get('url','')} |")
    lines += ['', '## Atualizações por eixo']
    for c in CATS: lines.append(f"- {c}: {sum(1 for r in rows if r.get('category')==c)}")
    lines += ['', '## Impacto nos artigos']
    for ws in ['busca1','busca2a','busca2b','a3']:
        lines.append(f"- {ws}: {sum(1 for r in rows if ws in (r.get('workstream_affinity') or []))}")
    host_fail={}
    for r in rows:
        if r.get('failure_reason'): host_fail[r.get('host','unknown')]=host_fail.get(r.get('host','unknown'),0)+1
    lines += ['', '## Falhas e limitações', f"- quantidade metadata_only: {cnt('metadata_only')}", f"- providers com falha: {sum(1 for r in rows if r.get('failure_reason'))}", '- observação: 403/paywall/login podem bloquear captura pública.']
    for h,n in sorted(host_fail.items(), key=lambda kv: kv[1], reverse=True)[:5]: lines.append(f"- host com falha: {h} ({n})")
    lines += ['', '## Ações sugeridas', '- Ler agora: top 3 itens de maior score.', '- Triagem humana: itens metadata_only de alta prioridade.', '- Considerar para Rayyan: revisões/trials/guidelines novos.', '- Monitorar próxima rodada: hosts com falhas recorrentes.']
    md.write_text('\n'.join(lines),encoding='utf-8'); js.write_text(json.dumps({'date':d,'total':len(rows),'items':rows},ensure_ascii=False,indent=2),encoding='utf-8')
    latest_doc_path.parent.mkdir(parents=True, exist_ok=True); latest_doc_path.write_text(md.read_text(encoding='utf-8'),encoding='utf-8'); return md,js
