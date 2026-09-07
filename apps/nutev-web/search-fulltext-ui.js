let latestResult=null;
let scheduled=false;

function statusText(meta){
  const status=String(meta?.status||'');
  if(status==='extracted'&&meta?.ocr_used)return'OCR aplicado · texto completo lido';
  if(status==='extracted'&&meta?.cache_hit)return'Texto completo lido · cache';
  if(status==='extracted')return'Texto completo lido';
  if(status==='candidate_available_not_processed')return'Texto completo candidato · não processado';
  if(status==='unreachable')return'Texto completo não alcançável';
  if(status==='not_found')return'Texto completo não localizado';
  if(status==='failed')return'Falha no enriquecimento de texto completo';
  return'';
}

function ensureStyles(){
  if(document.querySelector('#nutevFullTextStyles'))return;
  const style=document.createElement('style');
  style.id='nutevFullTextStyles';
  style.textContent=`
    .fulltext-summary{margin-top:.8rem;padding:.8rem .95rem;border:1px solid #d9e4df;border-radius:12px;background:#f8fbf9;display:flex;gap:.6rem;flex-wrap:wrap;align-items:center;font-size:.82rem;color:#42534e}
    .fulltext-summary strong{color:#183b32}
    .fulltext-indicator{margin-top:.65rem;padding:.58rem .7rem;border-radius:10px;background:#f4f8f6;border:1px solid #dce7e2;display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;font-size:.78rem;color:#4f625c}
    .fulltext-indicator strong{color:#1d5143}
    .fulltext-indicator[data-status="failed"],.fulltext-indicator[data-status="unreachable"]{background:#fff8f6;border-color:#f0d8d2}
    .fulltext-indicator .fulltext-detail{color:#667772}
  `;
  document.head.appendChild(style);
}

function resultIndex(card,position){
  const explicit=Number(card.dataset.resultIndex);
  return Number.isInteger(explicit)&&explicit>=0?explicit:position;
}

function decorateCards(){
  const rows=latestResult?.results||[];
  document.querySelectorAll('#results .result-card').forEach((card,position)=>{
    card.querySelector('.fulltext-indicator')?.remove();
    const row=rows[resultIndex(card,position)];
    const meta=row?.full_text;
    const label=statusText(meta);
    if(!label)return;
    const box=document.createElement('div');
    box.className='fulltext-indicator';
    box.dataset.status=String(meta.status||'');
    const strong=document.createElement('strong');
    strong.textContent=label;
    box.appendChild(strong);
    const details=[];
    if(meta.extraction_method)details.push(String(meta.extraction_method).replaceAll('_',' '));
    if(Number(meta.text_chars)>0)details.push(`${Number(meta.text_chars).toLocaleString('pt-BR')} caracteres extraídos`);
    if(meta.resolver_source)details.push(`via ${meta.resolver_source}`);
    if(meta.ranking_influence==='none')details.push('não altera o ranking');
    if(details.length){const span=document.createElement('span');span.className='fulltext-detail';span.textContent=details.join(' · ');box.appendChild(span)}
    card.appendChild(box);
  });
}

function decorateSummary(){
  const summary=document.querySelector('#summary');
  if(!summary)return;
  summary.querySelector('.fulltext-summary')?.remove();
  const data=latestResult?.full_text_enrichment;
  if(!data)return;
  const box=document.createElement('div');
  box.className='fulltext-summary';
  const lead=document.createElement('strong');
  const enabled=data.enabled===true;
  lead.textContent=enabled?'Enriquecimento seletivo de texto completo ativo':'Enriquecimento de texto completo não executado';
  box.appendChild(lead);
  if(enabled){
    const parts=[
      `${Number(data.selected||0)} selecionados`,
      `${Number(data.extracted||0)} textos completos lidos`,
      `${Number(data.ocr_used||0)} com OCR`,
      `${Number(data.cache_hits||0)} do cache`,
    ];
    const span=document.createElement('span');span.textContent=parts.join(' · ');box.appendChild(span);
  }
  const guard=document.createElement('span');guard.textContent='O corpo integral fica no servidor; o resultado público guarda apenas proveniência e métricas de extração. Full text não muda a posição no ranking.';box.appendChild(guard);
  summary.appendChild(box);
}

function decorate(){
  scheduled=false;
  if(!latestResult)return;
  ensureStyles();
  decorateSummary();
  decorateCards();
}

function schedule(){
  if(scheduled)return;
  scheduled=true;
  requestAnimationFrame(()=>requestAnimationFrame(decorate));
}

function observe(){
  const root=document.querySelector('main')||document.body;
  if(!root)return;
  new MutationObserver(schedule).observe(root,{childList:true,subtree:true});
}

window.addEventListener('nutev:search-result',event=>{
  latestResult=event.detail?.result||null;
  schedule();
});

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',observe,{once:true});
else observe();
