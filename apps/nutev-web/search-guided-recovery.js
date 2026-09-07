const $=selector=>document.querySelector(selector);
const esc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
let queryLintTimer=0;
let lastRecoveryKey='';

function currentMode(){return document.querySelector('input[name="searchMode"]:checked')?.value||'quick'}
function queryValue(){return $('#question')?.value.trim()||''}

function analyzeQuery(query,mode=currentMode()){
  const text=String(query||'');const issues=[];const suggestions=new Set();
  const quoteCount=(text.match(/"/g)||[]).length;
  if(quoteCount%2!==0){issues.push({severity:'warning',code:'unbalanced_quotes',message:'Há aspas duplas sem fechamento. Revise a frase antes de buscar.'});suggestions.add('review')}
  let depth=0;let earlyClose=false;
  for(const char of text){if(char==='(')depth+=1;if(char===')'){depth-=1;if(depth<0){earlyClose=true;depth=0}}}
  if(depth!==0||earlyClose){issues.push({severity:'warning',code:'unbalanced_parentheses',message:'Os parênteses parecem desbalanceados. O NutEV não vai corrigi-los automaticamente.'});suggestions.add('review')}
  const booleanOps=(text.match(/\b(?:AND|OR|NOT)\b/gi)||[]).length;
  if(mode==='quick'&&booleanOps>=4){issues.push({severity:'info',code:'complex_boolean',message:'A consulta contém vários operadores booleanos. Para controlar campos e blocos, prefira Busca avançada ou Estratégia exata.'});suggestions.add('advanced');suggestions.add('exact')}
  const words=text.split(/\s+/).filter(Boolean);
  if(text&&words.length===1&&text.length<=3){issues.push({severity:'info',code:'very_short',message:'A consulta é muito curta e pode ser ambígua. Você pode detalhar população, exposição/intervenção ou desfecho.'});suggestions.add('review')}
  if(mode==='quick'&&text.length>500){issues.push({severity:'info',code:'long_quick_query',message:'A consulta está longa para o modo rápido. Se a sintaxe for intencional, use Estratégia exata para preservá-la literalmente.'});suggestions.add('exact')}
  return{issues,suggestions:[...suggestions]};
}

function ensureAssist(){
  let root=$('#queryAssist');if(root)return root;
  const question=$('#question');if(!question)return null;
  root=document.createElement('div');root.id='queryAssist';root.className='query-assist';root.hidden=true;question.after(root);return root;
}
function renderQueryAssist(){
  const root=ensureAssist();if(!root)return;
  const analysis=analyzeQuery(queryValue());
  if(!analysis.issues.length){root.hidden=true;root.innerHTML='';return}
  const warning=analysis.issues.some(item=>item.severity==='warning');
  root.hidden=false;root.className=`query-assist ${warning?'warning':'info'}`;
  root.innerHTML=`<div><strong>${warning?'Revise a sintaxe':'Ajuste opcional da consulta'}</strong><ul>${analysis.issues.map(item=>`<li>${esc(item.message)}</li>`).join('')}</ul><small>O NutEV apenas sinaliza a estrutura. Não adiciona sinônimos, descritores MeSH/DeCS ou termos científicos sem sua ação.</small></div><div class="query-assist-actions">${analysis.suggestions.includes('advanced')?'<button type="button" class="ghost" data-query-mode="advanced">Usar Busca avançada</button>':''}${analysis.suggestions.includes('exact')?'<button type="button" class="ghost" data-query-mode="exact">Usar Estratégia exata</button>':''}</div>`;
  root.querySelectorAll('[data-query-mode]').forEach(button=>button.addEventListener('click',()=>activateMode(button.dataset.queryMode)));
}
function activateMode(mode){
  const radio=document.querySelector(`input[name="searchMode"][value="${mode}"]`);if(!radio)return;
  radio.click();
  $('#strategyBuilder')?.scrollIntoView({behavior:'smooth',block:'start'});
}

function providerGaps(result){
  const ids=new Set();
  for(const item of result?.providers||[]){if(['failed','unavailable','partial','skipped'].includes(String(item?.status||'')))ids.add(String(item?.provider||item?.id||item?.label||''))}
  for(const key of ['failed_providers','unavailable_providers','non_exhaustive_providers'])for(const item of result?.[key]||[])ids.add(String(typeof item==='string'?item:(item?.provider||item?.id||item?.label||'')));
  ids.delete('');return ids;
}
function isGlobalSearch(result){return String(result?.search_mode||'').includes('global_exhaustive')}
function recoveryKey(result){return String(result?.search_id||`${result?.query||''}|${result?.created_at||''}|${result?.returned_records||0}`)}

function ensureRecoveryPanel(){
  let panel=$('#searchRecovery');if(panel)return panel;
  const summary=$('#summary');if(!summary)return null;
  panel=document.createElement('section');panel.id='searchRecovery';panel.className='search-recovery card hidden';panel.setAttribute('aria-label','Recuperar ou ampliar a busca');
  summary.after(panel);return panel;
}
function resultCount(result){return Number(result?.returned_records??result?.results?.length??0)}
function recoveryModel(result){
  const count=resultCount(result);const gaps=providerGaps(result);const total=Array.isArray(result?.providers)?result.providers.length:0;const partial=gaps.size>0;
  if(count>5)return null;
  if(count===0&&partial)return{tone:'warning',title:'Nenhuma referência utilizável foi retornada e há lacunas de fonte.',body:`${gaps.size} de ${total||gaps.size} fonte(s) reportaram indisponibilidade, limitação ou cobertura parcial. Antes de mudar a pergunta, confira as fontes.`,zero:true,partial};
  if(count===0)return{tone:'neutral',title:'A busca terminou sem referências retornadas.',body:'Isso descreve somente esta recuperação nas fontes consultadas e não prova ausência de evidência. Você pode revisar a formulação ou ampliar a cobertura.',zero:true,partial};
  return{tone:'neutral',title:`A busca retornou apenas ${count} ${count===1?'referência':'referências'}.`,body:'O conjunto é pequeno, mas o NutEV não interpreta isso como evidência insuficiente. Use as opções abaixo apenas se quiser ampliar ou reformular a recuperação.',zero:false,partial};
}
function renderRecovery(result){
  const panel=ensureRecoveryPanel();if(!panel)return;
  const key=recoveryKey(result);const model=recoveryModel(result);lastRecoveryKey=key;
  if(!model){panel.className='search-recovery card hidden';panel.innerHTML='';return}
  const canGlobal=!isGlobalSearch(result);
  panel.className=`search-recovery card ${model.tone}`;
  panel.innerHTML=`<div class="search-recovery-head"><div><span class="recovery-eyebrow">Recuperação guiada</span><strong>${esc(model.title)}</strong><p>${esc(model.body)}</p></div><span class="recovery-boundary">Nenhuma opção abaixo altera sua consulta silenciosamente.</span></div><div class="search-recovery-actions"><button type="button" class="ghost" data-recovery="query">Revisar consulta</button><button type="button" class="ghost" data-recovery="sources">Revisar fontes</button>${canGlobal?'<button type="button" class="global-search" data-recovery="global">Tentar mesma pergunta com cobertura máxima</button>':''}<button type="button" class="ghost" data-recovery="advanced">Configurar Busca avançada</button><a class="ghost recovery-link" href="/search.html?view=history">Ver Minhas buscas</a></div>${model.partial?'<div class="recovery-note"><strong>Há lacunas de fonte.</strong> Resultados já recuperados continuam válidos como registros recuperados; a lacuna não deve ser reinterpretada como ausência de evidência.</div>':'<div class="recovery-note">Para ampliar, edite você mesmo os conceitos ou selecione cobertura máxima. O NutEV não expande termos científicos automaticamente.</div>'}`;
  panel.querySelector('[data-recovery="query"]')?.addEventListener('click',()=>{$('#question')?.focus();$('#question')?.scrollIntoView({behavior:'smooth',block:'center'})});
  panel.querySelector('[data-recovery="sources"]')?.addEventListener('click',()=>{const details=document.querySelector('details.advanced');details?.setAttribute('open','');details?.scrollIntoView({behavior:'smooth',block:'center'})});
  panel.querySelector('[data-recovery="advanced"]')?.addEventListener('click',()=>activateMode('advanced'));
  panel.querySelector('[data-recovery="global"]')?.addEventListener('click',()=>$('#globalSearchBtn')?.click());
}

function scheduleQueryLint(){clearTimeout(queryLintTimer);queryLintTimer=setTimeout(renderQueryAssist,180)}
$('#question')?.addEventListener('input',scheduleQueryLint);
document.querySelectorAll('input[name="searchMode"]').forEach(radio=>radio.addEventListener('change',renderQueryAssist));
window.addEventListener('nutev:search-result',event=>renderRecovery(event.detail?.result||{}));
window.addEventListener('nutev:search-job',()=>{const panel=$('#searchRecovery');if(panel)panel.classList.add('hidden')});
window.addEventListener('pageshow',()=>{renderQueryAssist();const result=window.NutEVSearchUX?.getLastResult?.();if(result&&lastRecoveryKey!==recoveryKey(result))renderRecovery(result)});

renderQueryAssist();
window.NutEVSearchRecovery={analyzeQuery,recoveryModel,renderRecovery};
