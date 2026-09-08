const $=selector=>document.querySelector(selector);
const esc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');

let context=null;

async function jsonFetch(url,options={}){
  const response=await fetch(url,{cache:'no-store',credentials:'same-origin',...options});
  let payload={};
  try{payload=await response.json()}catch{}
  if(!response.ok){const error=new Error(payload?.error||`http_${response.status}`);error.status=response.status;error.payload=payload;throw error}
  return payload;
}

function scopeValue(){
  const requested=$('#libraryScope')?.value==='project'?'project':'workspace';
  return requested==='project'&&context?.project_id?'project':'workspace';
}

function renderContext(){
  const label=$('#libraryContext');
  const select=$('#libraryScope');
  if(!context?.workspace_id){
    if(label)label.textContent='Selecione um workspace autenticado antes de usar a Evidence Library.';
    if(select)select.disabled=true;
    return;
  }
  if(label)label.textContent=context.project_id?`Workspace ${context.workspace_id} · projeto ${context.project_id}`:`Workspace ${context.workspace_id} · sem projeto selecionado`;
  if(select){select.disabled=false;const projectOption=select.querySelector('option[value="project"]');if(projectOption)projectOption.disabled=!context.project_id;if(!context.project_id&&select.value==='project')select.value='workspace'}
}

function entryHtml(item){
  const placement=item?.placement||{};
  const document=item?.document||{};
  const ids=[document.doi?`DOI ${document.doi}`:'',document.pmid?`PMID ${document.pmid}`:'',document.article_id||placement.article_id||''].filter(Boolean).join(' · ');
  const tags=(placement.tags||[]).map(tag=>`<span class="status-pill">${esc(tag)}</span>`).join(' ');
  return `<article class="history-item history-card" data-placement-id="${esc(placement.placement_id||'')}"><div><strong>${esc(document.title||'Documento sem título')}</strong><div class="history-meta">${esc(document.journal||'')}${document.year?` · ${esc(document.year)}`:''}</div><div class="history-meta">${esc(ids)}</div></div><div class="history-card-details"><div class="history-status-row"><span class="history-status ok">${esc(placement.state||'not_screened')}</span>${placement.project_id?'<span>Projeto</span>':'<span>Workspace</span>'}</div>${tags?`<div>${tags}</div>`:''}${placement.notes?`<p>${esc(placement.notes)}</p>`:''}<div class="history-actions"><button class="ghost" type="button" data-delete-placement="${esc(placement.placement_id||'')}">Remover placement</button><button class="ghost" type="button" data-fulltext-article="${esc(document.article_id||placement.article_id||'')}">Ver acesso ao texto completo</button></div><div class="history-meta" data-fulltext-status></div></div></article>`;
}

async function loadContext(){
  const payload=await jsonFetch('/api/context');
  context=payload.current||null;
  renderContext();
}

async function loadLibrary(){
  const state=$('#libraryStateMessage');
  const root=$('#libraryEntries');
  if(state)state.textContent='Carregando Evidence Library…';
  if(root)root.innerHTML='';
  if(!context?.workspace_id){if(state)state.textContent='Workspace não selecionado.';return}
  const scope=scopeValue();
  try{
    const payload=await jsonFetch(`/api/library?scope=${scope}&limit=500`);
    const entries=Array.isArray(payload.entries)?payload.entries:[];
    if(state)state.textContent=entries.length?`${entries.length.toLocaleString('pt-BR')} placement(s) neste escopo.`:'Nenhum placement neste escopo.';
    if(root)root.innerHTML=entries.map(entryHtml).join('');
  }catch(error){if(state)state.textContent=error.status===409?'Global Evidence Registry ainda não está materializado neste runtime.':'Não foi possível carregar a Evidence Library.'}
}

async function savePlacement(){
  const status=$('#librarySaveStatus');
  const articleId=String($('#libraryArticleId')?.value||'').trim();
  if(!articleId){if(status)status.textContent='Informe o article_id canônico.';return}
  const tags=String($('#libraryTags')?.value||'').split(',').map(value=>value.trim()).filter(Boolean);
  const body={article_id:articleId,scope:scopeValue(),state:$('#libraryState')?.value||'not_screened',tags,notes:String($('#libraryNotes')?.value||'')};
  if(status)status.textContent='Salvando…';
  try{
    await jsonFetch('/api/library/placements',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    if(status)status.textContent='Placement salvo no escopo privado.';
    await loadLibrary();
  }catch(error){if(status)status.textContent=error.status===404?'article_id não encontrado no Registry global.':error.status===403?'Seu papel não permite editar esta Library.':'Falha ao salvar placement.'}
}

async function deletePlacement(id){
  if(!id)return;
  try{await jsonFetch(`/api/library/placements/${encodeURIComponent(id)}`,{method:'DELETE'});await loadLibrary()}catch{await loadLibrary()}
}

async function showFullText(articleId,button){
  if(!articleId)return;
  const card=button.closest('[data-placement-id]');
  const target=card?.querySelector('[data-fulltext-status]');
  if(target)target.textContent='Verificando grants…';
  try{
    const payload=await jsonFetch(`/api/library/full-text/${encodeURIComponent(articleId)}`);
    const grants=Array.isArray(payload.grants)?payload.grants:[];
    if(target)target.innerHTML=grants.length?grants.map(grant=>`<span>${esc(grant.access_type||'acesso')} · redistribuição ${grant.redistribution_allowed?'permitida':'não permitida'}${grant.expires_at?` · expira ${esc(grant.expires_at)}`:''}</span>`).join('<br>'):'Nenhum grant de texto completo ativo neste contexto.';
  }catch{if(target)target.textContent='Acesso ao texto completo não disponível neste contexto.'}
}

async function init(){
  const health=$('#libraryHealth');
  try{const auth=await jsonFetch('/api/auth/status');if(auth.mode!=='pilot'){if(health)health.textContent='modo legacy';$('#libraryStateMessage').textContent='A Evidence Library multi-tenant fica disponível no modo pilot autenticado.';return}await loadContext();if(health)health.textContent=context?.workspace_id?'contexto autenticado':'workspace necessário';await loadLibrary()}catch{if(health)health.textContent='autenticação necessária';$('#libraryStateMessage').textContent='Faça login no piloto autenticado para acessar a Evidence Library.'}
}

$('#libraryScope')?.addEventListener('change',loadLibrary);
$('#refreshLibrary')?.addEventListener('click',loadLibrary);
$('#saveLibraryPlacement')?.addEventListener('click',savePlacement);
$('#libraryEntries')?.addEventListener('click',event=>{const deleteButton=event.target.closest('[data-delete-placement]');if(deleteButton){deletePlacement(deleteButton.dataset.deletePlacement);return}const fullTextButton=event.target.closest('[data-fulltext-article]');if(fullTextButton)showFullText(fullTextButton.dataset.fulltextArticle,fullTextButton)});

init();
