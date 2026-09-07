const SENTINEL='__NUTEV_MONITORING_ABANDONED__';
let activeJobId='';
let abandoning=false;

const $=selector=>document.querySelector(selector);

function ensureActions(){
  let root=$('#searchMonitorActions');
  if(root)return root;
  const state=$('#searchState');
  if(!state)return null;
  root=document.createElement('div');
  root.id='searchMonitorActions';
  root.className='search-monitor-actions hidden';
  root.setAttribute('aria-live','polite');
  state.insertAdjacentElement('afterend',root);
  return root;
}

function hideActions(){
  const root=ensureActions();
  if(!root)return;
  root.classList.add('hidden');
  root.innerHTML='';
  activeJobId='';
  abandoning=false;
}

function showActions(job){
  if(!job?.job_id||!['queued','running'].includes(job.status))return hideActions();
  activeJobId=String(job.job_id);
  const root=ensureActions();
  if(!root)return;
  root.classList.remove('hidden');
  root.innerHTML=`<div><strong>Esta busca pode continuar em segundo plano.</strong><span>Você pode parar apenas o acompanhamento desta tela. A execução no servidor não é cancelada e continuará disponível em Minhas buscas quando terminar.</span></div><button id="stopSearchMonitoring" type="button" class="ghost">Parar acompanhamento e fazer outra busca</button>`;
  $('#stopSearchMonitoring')?.addEventListener('click',()=>{
    if(abandoning||!activeJobId)return;
    const accepted=window.NutEVSearchEvents?.abandonJob?.(activeJobId)===true;
    if(!accepted)return;
    abandoning=true;
    const button=$('#stopSearchMonitoring');
    if(button){button.disabled=true;button.textContent='Encerrando acompanhamento…'}
  });
}

function showDetachedState(){
  const state=$('#searchState');
  if(!state)return;
  state.className='search-monitoring-detached';
  state.innerHTML='<strong>Acompanhamento encerrado.</strong><span>A busca continua no servidor. Você já pode iniciar outra consulta; quando a execução terminar, o resultado ficará disponível em Minhas buscas.</span>';
  $('#searchProgress')?.classList.add('hidden');
  hideActions();
  queueMicrotask(()=>$('#question')?.focus());
}

window.addEventListener('nutev:search-job',event=>{
  const job=event.detail?.job;
  if(job?.status==='queued'||job?.status==='running')showActions(job);
});
window.addEventListener('nutev:search-result',hideActions);
window.addEventListener('nutev:search-failed',hideActions);
window.addEventListener('nutev:search-monitoring-abandoned',()=>{
  $('#searchProgress')?.classList.add('hidden');
});

const state=$('#searchState');
if(state){
  new MutationObserver(()=>{
    if(state.textContent?.includes(SENTINEL))showDetachedState();
  }).observe(state,{childList:true,characterData:true,subtree:true});
}

window.addEventListener('pageshow',()=>{
  const job=window.NutEVSearchEvents?.getLastJob?.();
  if(job?.status==='queued'||job?.status==='running')showActions(job);
});
