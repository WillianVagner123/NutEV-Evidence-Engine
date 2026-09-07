const $=selector=>document.querySelector(selector);
const esc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');

let activeJobId='';
let searchStartedAt=0;
let elapsedTimer=0;
let lastJob=null;
let lastResult=null;
let lastOutcomeKey='';

function feedbackElement(){return $('#searchFeedback')}
function showFeedback(message,kind='error'){
  const root=feedbackElement();if(!root)return;
  root.className=`search-feedback ${kind}`;
  root.innerHTML=`<strong>${kind==='error'?'Revise antes de continuar':'Atenção'}</strong><span>${esc(message)}</span>`;
  root.removeAttribute('hidden');
}
function clearFeedback(){const root=feedbackElement();if(!root)return;root.setAttribute('hidden','');root.textContent=''}

// The public search should never interrupt the user with modal browser alerts.
window.alert=message=>{
  const text=String(message||'Não foi possível concluir esta ação.');
  showFeedback(text,'error');
  if(/digite/i.test(text))$('#question')?.focus();
  if(/selecione pelo menos uma fonte/i.test(text))document.querySelector('details.advanced')?.setAttribute('open','');
};

function elapsedLabel(){
  if(!searchStartedAt)return'';
  const seconds=Math.max(0,Math.floor((Date.now()-searchStartedAt)/1000));
  if(seconds<60)return`${seconds}s`;
  const minutes=Math.floor(seconds/60);return`${minutes}min ${seconds%60}s`;
}
function stageLabel(job){
  if(job?.stage==='finalizing')return'Deduplicando e ordenando as referências';
  if(job?.stage==='persisting')return'Salvando a busca para você recuperar depois';
  if(job?.status==='queued')return'Preparando as fontes';
  return'Consultando fontes científicas';
}
function renderElapsed(){if(lastJob&&activeJobId)renderProgress(lastJob)}
function beginProgress(job){
  activeJobId=String(job?.job_id||activeJobId||'');
  if(!searchStartedAt)searchStartedAt=Date.now();
  if(!elapsedTimer)elapsedTimer=window.setInterval(renderElapsed,1000);
  renderProgress(job);
}
function finishProgress(){
  activeJobId='';searchStartedAt=0;lastJob=null;
  if(elapsedTimer){clearInterval(elapsedTimer);elapsedTimer=0}
  const root=$('#searchProgress');if(root){root.classList.add('hidden');root.removeAttribute('data-reconnecting')}
}
function renderProgress(job){
  lastJob=job;
  const root=$('#searchProgress');if(!root)return;
  const completed=Number(job?.completed_providers||0);const total=Number(job?.total_providers||0);
  const percent=total?Math.max(0,Math.min(100,Math.round((completed/total)*100))):8;
  const providers=Array.isArray(job?.providers)?job.providers:[];
  const running=providers.find(item=>item.status==='running');
  const reconnecting=root.dataset.reconnecting==='true';
  root.classList.remove('hidden');
  root.setAttribute('aria-busy',String(job?.status!=='completed'&&job?.status!=='failed'));
  root.innerHTML=`<div class="search-progress-head"><div><strong>${esc(stageLabel(job))}</strong><span>${total?`${completed} de ${total} fontes concluídas`:'aguardando plano de fontes'} · ${esc(elapsedLabel())}</span></div><span class="search-progress-provider">${running?`Agora: ${esc(running.label||running.provider||'fonte')}`:(job?.stage==='finalizing'?'Consolidando resultados':'')}</span></div><div class="search-progress-track" role="progressbar" aria-label="Progresso da busca" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${percent}"><span style="width:${percent}%"></span></div>${reconnecting?'<div class="search-reconnect">A conexão oscilou. O NutEV está tentando recuperar o acompanhamento sem repetir a busca.</div>':''}<div class="search-progress-foot">Você pode sair desta página: a execução é persistida no servidor e poderá aparecer em <a href="/search.html?view=history">Minhas buscas</a>.</div>`;
  root.removeAttribute('data-reconnecting');
}

function providerGapIds(data){
  const gaps=new Set();
  for(const item of data?.providers||[]){if(['failed','unavailable','partial','skipped'].includes(String(item?.status||'')))gaps.add(String(item.provider||item.id||item.label||''))}
  for(const key of ['failed_providers','unavailable_providers','partial_providers','skipped_providers','non_exhaustive_providers'])for(const item of data?.[key]||[])gaps.add(String(typeof item==='string'?item:(item?.provider||item?.id||item?.label||'')));
  gaps.delete('');return gaps;
}
function summaryGapCount(data){return providerGapIds(data).size+(Array.isArray(data?.audit_gaps)?data.audit_gaps.length:0)}
function providerDisplayName(data,id){
  const match=(data?.providers||[]).find(item=>String(item.provider||item.id||item.label||'')===id);
  return String(match?.label||id).replaceAll('_',' ');
}
function coverageOutcome(data){
  const providers=Array.isArray(data?.providers)?data.providers:[];const total=providers.length;
  const gaps=providerGapIds(data);const recovered=Number(data?.returned_records||data?.results?.length||0);const unique=Number(data?.unique_records||0);
  const healthy=Math.max(0,total-gaps.size);
  if(recovered>0&&gaps.size===0)return{kind:'ok',title:'Busca concluída',detail:`${unique.toLocaleString('pt-BR')} referências únicas · ${total?`${healthy} de ${total} fontes sem lacuna reportada`:'fontes concluídas'}`};
  if(recovered>0)return{kind:'partial',title:'Busca concluída com cobertura parcial',detail:`${unique.toLocaleString('pt-BR')} referências únicas · ${healthy} de ${total} fontes sem lacuna reportada`,gaps:[...gaps].map(id=>providerDisplayName(data,id))};
  if(total>0&&healthy>0)return{kind:'empty',title:'Busca concluída sem resultados retornados',detail:`${healthy} de ${total} fontes concluíram sem lacuna reportada. Isso não prova ausência de evidência.`};
  return{kind:'bad',title:'A busca não recuperou resultados utilizáveis',detail:'As fontes selecionadas apresentaram indisponibilidade ou lacunas suficientes para impedir um conjunto utilizável.',gaps:[...gaps].map(id=>providerDisplayName(data,id))};
}

function queueSummaryEnhancement(data){
  window.setTimeout(()=>enhanceSummary(data),0);
  window.setTimeout(()=>enhanceSummary(data),80);
}
function enhanceSummary(data){
  const summary=$('#summary');if(!summary||summary.classList.contains('hidden'))return;
  const key=String(data?.search_id||`${data?.query||''}|${data?.returned_records||0}`);
  const outcome=coverageOutcome(data);
  const kpiValues=summary.querySelectorAll('.summary-grid .kpi strong');
  if(kpiValues.length>=4)kpiValues[3].textContent=String(summaryGapCount(data));
  summary.querySelector('.search-outcome')?.remove();
  const banner=document.createElement('div');banner.className=`search-outcome ${outcome.kind}`;
  banner.innerHTML=`<div><strong>${esc(outcome.title)}</strong><span>${esc(outcome.detail)}</span>${outcome.gaps?.length?`<small>Cobertura parcial em: ${outcome.gaps.slice(0,6).map(esc).join(', ')}${outcome.gaps.length>6?'…':''}</small>`:''}</div><span class="outcome-boundary">Cobertura descreve recuperação das fontes, não qualidade, certeza ou elegibilidade da evidência.</span>`;
  summary.insertBefore(banner,summary.firstChild);
  summary.querySelectorAll('details.plan-audit').forEach(details=>details.removeAttribute('open'));
  let technical=summary.querySelector('.search-technical-details');
  if(!technical){
    const movable=[...summary.children].filter(node=>node!==banner&&(node.matches?.('details.plan-audit')||node.matches?.('.review-result-note')||node.matches?.('.warning')));
    if(movable.length){
      technical=document.createElement('details');technical.className='search-technical-details';technical.innerHTML='<summary>Detalhes técnicos da busca</summary><div class="search-technical-body"></div>';
      const body=technical.querySelector('.search-technical-body');movable.forEach(node=>body.appendChild(node));summary.appendChild(technical);
    }
  }
  lastOutcomeKey=key;
  compactCards();
}

function compactCards(){
  document.querySelectorAll('#results .result-card').forEach(card=>{
    const abstract=card.querySelector(':scope > .abstract');
    if(abstract&&!abstract.closest('.abstract-details')){
      const details=document.createElement('details');details.className='abstract-details';
      const summary=document.createElement('summary');summary.textContent='Ver resumo do artigo';details.append(summary);abstract.before(details);details.append(abstract);
    }
    const signals=card.querySelector(':scope > .result-signals');
    if(signals&&!signals.closest('.classification-details')){
      const details=document.createElement('details');details.className='classification-details';
      const summary=document.createElement('summary');summary.textContent='Como foi classificado';details.append(summary);signals.before(details);details.append(signals);
    }
    card.dataset.uxCompacted='true';
  });
}

function prepareSearch(){
  clearFeedback();
  const query=$('#question')?.value.trim()||'';
  if(query){const url=new URL(location.href);url.searchParams.set('q',query);url.searchParams.delete('view');history.replaceState(null,'',`${url.pathname}?${url.searchParams.toString()}`)}
}

$('#searchBtn')?.addEventListener('click',prepareSearch,{capture:true});
$('#globalSearchBtn')?.addEventListener('click',prepareSearch,{capture:true});
$('#question')?.addEventListener('keydown',event=>{
  if(event.key==='Enter'&&(event.ctrlKey||event.metaKey)){
    event.preventDefault();$('#searchBtn')?.click();
  }
});

window.addEventListener('nutev:search-job',event=>{clearFeedback();beginProgress(event.detail?.job||{})});
window.addEventListener('nutev:search-result',event=>{
  const result=event.detail?.result;if(!result)return;
  lastResult=result;finishProgress();queueSummaryEnhancement(result);
});
window.addEventListener('nutev:search-failed',()=>finishProgress());
window.addEventListener('nutev:search-transport-retry',()=>{
  const progress=$('#searchProgress');if(progress&&!progress.classList.contains('hidden')){
    progress.dataset.reconnecting='true';if(lastJob)renderProgress(lastJob);
  }
});

const searchState=$('#searchState');
if(searchState)new MutationObserver(()=>{
  if(searchState.classList.contains('error'))finishProgress();
}).observe(searchState,{attributes:true,attributeFilter:['class']});

const results=$('#results');
if(results)new MutationObserver(()=>window.requestAnimationFrame(compactCards)).observe(results,{childList:true,subtree:true});

const summary=$('#summary');
if(summary)new MutationObserver(()=>{if(lastResult&&!summary.classList.contains('hidden')&&lastOutcomeKey!==String(lastResult?.search_id||`${lastResult?.query||''}|${lastResult?.returned_records||0}`))queueSummaryEnhancement(lastResult)}).observe(summary,{childList:true,attributes:true,attributeFilter:['class']});

window.addEventListener('pageshow',()=>{
  compactCards();
  const cached=window.NutEVSearchEvents?.getLastResult?.()||lastResult;
  if(cached){lastResult=cached;queueSummaryEnhancement(cached)}
});
window.NutEVSearchUX={showFeedback,clearFeedback,coverageOutcome,providerGapIds,summaryGapCount,compactCards,getLastResult:()=>window.NutEVSearchEvents?.getLastResult?.()||lastResult};