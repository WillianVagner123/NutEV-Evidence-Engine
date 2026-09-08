import{canonicalSavedKey,saveArticle,saveArticles,savedKeySet}from'./saved-library.js';

let latestSearch=null;
let enhanceToken=0;
let enhanceScheduled=false;
let modePromise=null;

function esc(value){return String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')}
function searchContext(data){return{search_id:data?.search_id||'',query:data?.query||'',search_mode:data?.search_mode||''}}
function resultForKey(key){return(latestSearch?.results||[]).find(item=>canonicalSavedKey(item)===key)||null}

async function runtimeMode(){
  if(!modePromise)modePromise=fetch('/api/auth/status',{cache:'no-store',credentials:'same-origin'}).then(async response=>{if(!response.ok)throw new Error(`auth_status_${response.status}`);const payload=await response.json();return payload?.mode==='pilot'?'pilot':'legacy'}).catch(()=> 'unknown');
  return modePromise;
}

async function canonicalLibraryHref(record=null,key=''){
  const mode=await runtimeMode();
  if(mode==='pilot'){
    const articleId=String(record?.article_id||'').trim();
    return articleId?`/evidence-library.html?article=${encodeURIComponent(articleId)}`:'/evidence-library.html';
  }
  return key?`/articles.html?saved=${encodeURIComponent(key)}`:'/articles.html';
}

function captureResult(result){
  if(!result?.results)return;
  latestSearch=result;
  scheduleEnhance();
}

window.addEventListener('nutev:search-result',event=>captureResult(event.detail?.result));

async function markSavedButtons(){
  const buttons=[...document.querySelectorAll('[data-save-library-key]')];
  if(!buttons.length)return;
  const keys=buttons.map(button=>button.dataset.saveLibraryKey);
  try{
    const saved=await savedKeySet(keys);
    for(const button of buttons){
      const isSaved=saved.has(button.dataset.saveLibraryKey);
      button.textContent=isSaved?'Guardado ✓':'Guardar na Biblioteca';
      button.classList.toggle('saved',isSaved);
      button.setAttribute('aria-pressed',String(isSaved));
      button.title=isSaved?'Este artigo já está na biblioteca do contexto atual.':'Guardar no workspace/projeto selecionado.';
    }
  }catch{
    for(const button of buttons){button.title='Não foi possível consultar a biblioteca do contexto atual.'}
  }
}

async function saveKey(key,{openLibrary=false}={}){
  const record=resultForKey(key);if(!record)return;
  const buttons=[...document.querySelectorAll('[data-save-library-key]')].filter(button=>button.dataset.saveLibraryKey===key);
  buttons.forEach(button=>{button.disabled=true;button.textContent='Guardando…'});
  try{
    await saveArticle(record,searchContext(latestSearch));
    buttons.forEach(button=>{button.textContent='Guardado ✓';button.classList.add('saved');button.setAttribute('aria-pressed','true')});
    if(openLibrary)location.href=await canonicalLibraryHref(record,key);
  }catch(error){
    const message=String(error?.message||'');
    const userMessage=message.includes('global_article_id_required')?'Este resultado ainda não possui identidade canônica para ser guardado.':message.includes('workspace_context_required')?'Selecione um workspace antes de guardar.':'Não foi possível guardar neste contexto.';
    buttons.forEach(button=>{button.textContent='Tentar guardar novamente';button.title=userMessage});
  }finally{buttons.forEach(button=>{button.disabled=false})}
}

async function saveAll(){
  const button=document.querySelector('#saveAllSearchResults');
  const results=latestSearch?.results||[];if(!button||!results.length)return;
  button.disabled=true;button.textContent=`Guardando ${results.length.toLocaleString('pt-BR')}…`;
  try{
    const outcome=await saveArticles(results,searchContext(latestSearch));
    const scopeCopy=outcome.scope==='project'?'projeto atual':outcome.scope==='workspace'?'workspace atual':'biblioteca';
    button.textContent=`${scopeCopy} atualizado · ${outcome.total.toLocaleString('pt-BR')}`;
    await markSavedButtons();
  }catch(error){button.textContent='Falha ao guardar resultados';button.title=error.message||''}
  finally{button.disabled=false}
}

async function ensureSummaryActions(){
  const summary=document.querySelector('#summary');if(!summary||summary.classList.contains('hidden')||!latestSearch?.results?.length)return;
  let bar=summary.querySelector('.search-library-bar');
  const mode=await runtimeMode();
  const libraryHref=await canonicalLibraryHref();
  const copy=mode==='pilot'?'Guarde os resultados no workspace/projeto selecionado. Isso não cria inclusão científica nem altera o documento global.':'Guarde os resultados localmente neste navegador sem alterar o corpus científico verificado.';
  if(!bar){
    bar=document.createElement('div');bar.className='search-library-bar';
    bar.innerHTML=`<div><strong>Biblioteca</strong><span></span></div><div class="search-library-buttons"><button class="ghost" type="button" id="saveAllSearchResults">Guardar todos os resultados retornados</button><a>Abrir Biblioteca →</a></div>`;
    summary.appendChild(bar);
    bar.querySelector('#saveAllSearchResults').addEventListener('click',saveAll);
  }
  bar.querySelector('div>span').textContent=copy;
  bar.querySelector('.search-library-buttons a').href=libraryHref;
}

async function ensureCardActions(){
  const cards=[...document.querySelectorAll('#results .result-card')];
  const results=latestSearch?.results||[];
  const mode=await runtimeMode();
  cards.forEach((card,index)=>{
    const taggedIndex=Number(card.dataset.resultIndex);
    const resultIndex=Number.isInteger(taggedIndex)&&taggedIndex>=0?taggedIndex:index;
    const record=results[resultIndex];if(!record)return;
    const key=canonicalSavedKey(record);
    let existing=card.querySelector('.saved-library-actions');
    if(existing?.dataset.savedLibraryKey!==key){existing?.remove();existing=null}
    if(!existing){
      let links=card.querySelector('.links');
      if(!links){links=document.createElement('div');links.className='links';card.appendChild(links)}
      const actions=document.createElement('span');actions.className='saved-library-actions';actions.dataset.savedLibraryKey=key;
      actions.innerHTML=`<button class="ghost" type="button" data-save-library-key="${esc(key)}" aria-pressed="false">Guardar na Biblioteca</button><button class="ghost" type="button" data-open-saved-key="${esc(key)}">${mode==='pilot'?'Abrir na Biblioteca':'Abrir dossiê'}</button>`;
      links.prepend(actions);
      actions.querySelector('[data-save-library-key]').addEventListener('click',event=>saveKey(event.currentTarget.dataset.saveLibraryKey));
      actions.querySelector('[data-open-saved-key]').addEventListener('click',event=>saveKey(event.currentTarget.dataset.openSavedKey,{openLibrary:true}));
    }else{
      const openButton=existing.querySelector('[data-open-saved-key]');
      if(openButton)openButton.textContent=mode==='pilot'?'Abrir na Biblioteca':'Abrir dossiê';
    }
  });
}

async function enhance(){
  enhanceScheduled=false;
  const token=++enhanceToken;if(!latestSearch)return;
  await Promise.all([ensureSummaryActions(),ensureCardActions()]);
  await markSavedButtons();
  if(token!==enhanceToken)return;
}

function scheduleEnhance(){
  if(enhanceScheduled)return;
  enhanceScheduled=true;
  requestAnimationFrame(()=>enhance());
}

const observer=new MutationObserver(mutations=>{
  if(!latestSearch)return;
  const relevant=mutations.some(mutation=>[...mutation.addedNodes].some(node=>node.nodeType===Node.ELEMENT_NODE&&(node.matches?.('#summary,#results,.result-card')||node.querySelector?.('#summary,#results,.result-card'))));
  if(relevant)scheduleEnhance();
});
observer.observe(document.documentElement,{subtree:true,childList:true});
window.addEventListener('pageshow',()=>{const cached=window.NutEVSearchEvents?.getLastResult?.();if(cached)captureResult(cached);else scheduleEnhance()});
