const $=selector=>document.querySelector(selector);
const esc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');

let latestHistory=[];
let latestScope='';
let scheduled=false;

function normalize(value){return String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR')}
function byId(){return new Map(latestHistory.map(item=>[String(item?.search_id||''),item]))}
function gapCount(item){
  const providerKeys=['failed_providers','unavailable_providers','partial_providers','skipped_providers','non_exhaustive_providers'];
  const providers=new Set();
  for(const key of providerKeys)for(const value of item?.[key]||[])providers.add(String(typeof value==='string'?value:(value?.provider||value?.id||value?.label||'')));
  providers.delete('');
  return providers.size+(item?.audit_gaps||[]).length;
}
function statusModel(item){
  const gaps=gapCount(item);const raw=String(item?.status||'').trim();
  if(raw==='COMPLETE_WITH_AUDIT_GAPS')return{label:'Concluída com lacunas de auditoria',tone:'partial'};
  if(raw==='COMPLETE_WITH_PROVIDER_GAPS'||gaps>0)return{label:'Concluída com lacunas',tone:'partial'};
  if(raw==='COMPLETE')return{label:'Concluída',tone:'ok'};
  if(/fail|error/i.test(raw))return{label:'Falhou',tone:'bad'};
  return{label:raw||'Status não informado',tone:'neutral'};
}
function dateLabel(value){
  const date=new Date(value);if(Number.isNaN(date.getTime()))return'Sem data';
  return date.toLocaleString('pt-BR',{dateStyle:'short',timeStyle:'short'});
}

function switchToSearchWorkspace(){
  document.querySelectorAll('.view').forEach(view=>view.classList.add('hidden'));
  $('#searchView')?.classList.remove('hidden');
  document.querySelectorAll('.nav-item[data-view]').forEach(item=>item.classList.toggle('active',item.dataset.view==='search'));
}
function clearPreviousSearchPresentation(){
  const summary=$('#summary');if(summary)summary.classList.add('hidden');
  const results=$('#results');if(results)results.innerHTML='';
  const recovery=$('#searchRecovery');if(recovery){recovery.classList.add('hidden');recovery.innerHTML=''}
  const progress=$('#searchProgress');if(progress){progress.classList.add('hidden');progress.innerHTML=''}
  const state=$('#searchState');if(state){state.className='hidden';state.textContent=''}
  $('#resultFacetWorkspace')?.classList.add('hidden');
}
function prepareNewQuickSearch(item){
  const query=String(item?.query||'').trim();if(!query)return;
  switchToSearchWorkspace();
  clearPreviousSearchPresentation();
  const quick=document.querySelector('input[name="searchMode"][value="quick"]');quick?.click();
  const question=$('#question');
  if(question){question.value=query;question.dispatchEvent(new Event('input',{bubbles:true}))}
  const url=new URL(location.href);url.searchParams.delete('view');url.searchParams.delete('q');history.replaceState(null,'',`${url.pathname}${url.search}${url.hash}`);
  question?.focus();question?.scrollIntoView({behavior:'smooth',block:'center'});
  window.NutEVSearchUX?.showFeedback?.('Pergunta carregada. Revise fontes e termos; a nova busca só começa quando você clicar em “Buscar artigos”.','warning');
}

async function loadHistoryScope(scope){
  const requested=scope==='project'?'project':'workspace';
  const message=$('#historyScopeMessage');if(message)message.textContent='Atualizando histórico…';
  try{
    const loader=window.NutEVSearchEvents?.loadHistoryScope;
    if(typeof loader!=='function')throw new Error('history_event_bus_unavailable');
    await loader(requested,50);
    if(message)message.textContent='';
  }catch(error){
    const status=Number(error?.status||0);
    if(message)message.textContent=status===409&&requested==='project'?'Selecione um projeto acessível para ver as buscas desse projeto.':'Não foi possível atualizar este histórico agora.';
  }
}

function scopeControls(){
  if(!['workspace','project'].includes(latestScope))return'';
  return `<div class="history-scope-switch" role="group" aria-label="Escopo do histórico"><button type="button" class="ghost${latestScope==='workspace'?' active':''}" data-history-scope="workspace">Buscas do workspace</button><button type="button" class="ghost${latestScope==='project'?' active':''}" data-history-scope="project">Buscas do projeto</button><span id="historyScopeMessage" aria-live="polite"></span></div>`;
}

function ensureToolbar(root){
  let toolbar=root.querySelector(':scope > .history-workspace');
  if(toolbar){
    const existing=toolbar.querySelector('.history-scope-switch');
    if(existing)existing.outerHTML=scopeControls();
    else if(scopeControls())toolbar.insertAdjacentHTML('afterbegin',scopeControls());
    bindScopeButtons(toolbar);
    return toolbar;
  }
  toolbar=document.createElement('div');toolbar.className='history-workspace';
  toolbar.innerHTML=`${scopeControls()}<div class="history-workspace-copy"><strong>Memória das suas buscas</strong><span>Abra uma execução já salva ou reutilize somente a pergunta para preparar uma nova busca.</span></div><label class="history-filter">Buscar no histórico<input id="historyFilter" type="search" autocomplete="off" placeholder="Filtrar por pergunta ou status"></label><div id="historyVisibleCount" class="history-visible-count" aria-live="polite"></div>`;
  root.prepend(toolbar);
  toolbar.querySelector('#historyFilter').addEventListener('input',applyFilter);
  bindScopeButtons(toolbar);
  return toolbar;
}

function bindScopeButtons(toolbar){
  toolbar.querySelectorAll('[data-history-scope]').forEach(button=>{
    if(button.dataset.bound==='true')return;
    button.dataset.bound='true';
    button.addEventListener('click',()=>loadHistoryScope(button.dataset.historyScope));
  });
}

function enrichItem(node,item){
  if(node.dataset.historyEnhanced==='true')return;
  const openButton=node.querySelector('button[data-id]');if(!openButton)return;
  const status=statusModel(item);const gaps=gapCount(item);const query=String(item?.query||'Busca sem pergunta registrada');
  node.dataset.historyEnhanced='true';node.dataset.historySearch=normalize(`${query} ${status.label} ${item?.status||''}`);
  node.classList.add('history-card');
  openButton.classList.add('history-open');
  openButton.setAttribute('aria-label',`Abrir resultados: ${query}`);
  openButton.innerHTML=`<span class="history-query">${esc(query)}</span><span class="history-open-label">Abrir resultados</span>`;
  const oldMeta=node.querySelector('.history-meta');oldMeta?.remove();
  const details=document.createElement('div');details.className='history-card-details';
  const projectLabel=item?.project_id?'<span>Projeto</span>':'<span>Workspace</span>';
  details.innerHTML=`<div class="history-status-row"><span class="history-status ${status.tone}">${esc(status.label)}</span><span>${esc(dateLabel(item?.created_at))}</span>${projectLabel}</div><div class="history-counts"><span><strong>${Number(item?.unique_records||0).toLocaleString('pt-BR')}</strong> únicas</span><span><strong>${Number(item?.returned_records||0).toLocaleString('pt-BR')}</strong> exibidas</span><span class="${gaps?'has-gaps':''}"><strong>${gaps}</strong> lacuna${gaps===1?'':'s'} de fonte/auditoria</span></div><div class="history-actions"><button type="button" class="ghost" data-prepare-search="${esc(String(item?.search_id||''))}">Usar pergunta em nova busca</button></div>`;
  node.appendChild(details);
  details.querySelector('[data-prepare-search]')?.addEventListener('click',()=>prepareNewQuickSearch(item));
}

function applyFilter(){
  const root=$('#historyList');if(!root)return;
  const needle=normalize(root.querySelector('#historyFilter')?.value||'');
  const cards=[...root.querySelectorAll('.history-item.history-card')];let visible=0;
  cards.forEach(card=>{const show=!needle||String(card.dataset.historySearch||'').includes(needle);card.hidden=!show;if(show)visible+=1});
  const count=root.querySelector('#historyVisibleCount');if(count)count.textContent=`${visible.toLocaleString('pt-BR')} de ${cards.length.toLocaleString('pt-BR')} buscas`;
}

function enhanceHistory(){
  scheduled=false;
  const root=$('#historyList');if(!root)return;
  if(latestHistory.length){
    const items=[...root.querySelectorAll(':scope > .history-item')];
    if(items.length){
      ensureToolbar(root);
      const map=byId();
      items.forEach(node=>{const id=String(node.querySelector('button[data-id]')?.dataset.id||'');const item=map.get(id);if(item)enrichItem(node,item)});
      applyFilter();
      return;
    }
  }
  if(['workspace','project'].includes(latestScope))ensureToolbar(root);
}
function scheduleEnhance(){if(scheduled)return;scheduled=true;requestAnimationFrame(enhanceHistory)}

window.addEventListener('nutev:search-history',event=>{
  latestHistory=Array.isArray(event.detail?.searches)?event.detail.searches:[];
  latestScope=String(event.detail?.scope||'');
  scheduleEnhance();
});
const historyRoot=$('#historyList');
if(historyRoot)new MutationObserver(scheduleEnhance).observe(historyRoot,{childList:true});
window.addEventListener('pageshow',()=>{const cached=window.NutEVSearchEvents?.getLastHistory?.()||[];if(cached.length){latestHistory=cached;scheduleEnhance()}});

window.NutEVSearchHistory={prepareNewQuickSearch,statusModel,gapCount,loadHistoryScope};
