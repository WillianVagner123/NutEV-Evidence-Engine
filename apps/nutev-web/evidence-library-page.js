const $=selector=>document.querySelector(selector)
const esc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')

let contextPayload=null
let entriesCache=[]
const STATE_LABELS={not_screened:'Não triado',included:'Incluído',excluded:'Excluído',background:'Contexto / background'}

async function jsonFetch(url,options={}){
  const response=await fetch(url,{cache:'no-store',credentials:'same-origin',...options})
  let payload={}
  try{payload=await response.json()}catch{}
  if(!response.ok){const error=new Error(payload?.error||`http_${response.status}`);error.status=response.status;error.payload=payload;throw error}
  return payload
}

function normalize(value){return String(value??'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR').replace(/\s+/g,' ').trim()}
function current(){return contextPayload?.current||{}}
function nameFor(items,id){return(items||[]).find(item=>item.id===id)?.name||''}
function scopeValue(){
  const requested=$('#libraryScope')?.value==='project'?'project':'workspace'
  return requested==='project'&&current().project_id?'project':'workspace'
}

function renderContext(){
  const selected=current()
  const label=$('#libraryContext')
  const title=$('#libraryContextTitle')
  const select=$('#libraryScope')
  if(!selected.workspace_id){
    if(title)title.textContent='Selecione um workspace'
    if(label)label.textContent='Escolha um workspace no seletor acima antes de usar a biblioteca.'
    if(select)select.disabled=true
    return
  }
  const workspaceName=nameFor(contextPayload.workspaces,selected.workspace_id)||'Workspace'
  const projectName=nameFor(contextPayload.projects,selected.project_id)||''
  if(title)title.textContent=scopeValue()==='project'&&projectName?projectName:workspaceName
  if(label)label.textContent=projectName?`${workspaceName} / ${projectName}`:`${workspaceName} · biblioteca compartilhada do workspace`
  if(select){
    select.disabled=false
    const projectOption=select.querySelector('option[value="project"]')
    if(projectOption)projectOption.disabled=!selected.project_id
    if(!selected.project_id&&select.value==='project')select.value='workspace'
  }
}

function stateLabel(value){return STATE_LABELS[String(value||'not_screened')]||String(value||'Não triado')}
function entrySearchText(item){
  const placement=item?.placement||{}
  const document=item?.document||{}
  return normalize([document.title,document.journal,document.doi,document.pmid,document.pmcid,document.article_id,...(placement.tags||[]),placement.notes,stateLabel(placement.state)].join(' '))
}

function entryHtml(item){
  const placement=item?.placement||{}
  const document=item?.document||{}
  const articleId=document.article_id||placement.article_id||''
  const ids=[document.doi?`DOI ${document.doi}`:'',document.pmid?`PMID ${document.pmid}`:''].filter(Boolean)
  const tags=(placement.tags||[]).map(tag=>`<span class="status-pill">${esc(tag)}</span>`).join(' ')
  const state=String(placement.state||'not_screened')
  return `<article class="library-entry" data-placement-id="${esc(placement.placement_id||'')}" data-article-id="${esc(articleId)}"><div><h3>${esc(document.title||'Documento sem título')}</h3><div class="library-entry-meta"><span>${esc(document.journal||'Periódico não informado')}</span>${document.year?`<span>· ${esc(document.year)}</span>`:''}${ids.map(id=>`<span>· ${esc(id)}</span>`).join('')}</div>${tags?`<div class="component-list">${tags}</div>`:''}</div><div class="library-entry-side"><span class="library-state-pill ${esc(state)}">${esc(stateLabel(state))}</span>${placement.notes?`<p class="library-notes">${esc(placement.notes)}</p>`:''}<div class="library-entry-actions"><button type="button" data-fulltext-article="${esc(articleId)}">Texto completo</button><button type="button" data-delete-placement="${esc(placement.placement_id||'')}">Remover da biblioteca</button></div><div class="history-meta" data-fulltext-status></div></div></article>`
}

function visibleEntries(){
  const query=normalize($('#libraryFilter')?.value||'')
  const state=$('#libraryStateFilter')?.value||''
  return entriesCache.filter(item=>{
    const placement=item?.placement||{}
    if(state&&placement.state!==state)return false
    return!query||entrySearchText(item).includes(query)
  })
}

function renderEntries(){
  const root=$('#libraryEntries')
  const state=$('#libraryStateMessage')
  const entries=visibleEntries()
  if(!entriesCache.length){
    state.textContent='Nenhum artigo nesta biblioteca.'
    root.innerHTML='<div class="empty-state"><strong>Biblioteca vazia</strong><span>Guarde artigos a partir dos resultados de busca. Isso preserva a identidade bibliográfica e cria somente o estado privado deste contexto.</span></div>'
    return
  }
  if(!entries.length){
    state.textContent='Nenhum artigo corresponde aos filtros atuais.'
    root.innerHTML='<div class="empty-state"><strong>Nenhum resultado</strong><span>Altere o texto de busca, o estado ou o escopo para ampliar a visualização.</span></div>'
    return
  }
  state.textContent=`${entries.length.toLocaleString('pt-BR')} de ${entriesCache.length.toLocaleString('pt-BR')} artigo(s) visível(is) neste escopo.`
  root.innerHTML=entries.map(entryHtml).join('')
  const wanted=new URLSearchParams(location.search).get('article')
  if(wanted){
    const card=[...root.querySelectorAll('[data-article-id]')].find(node=>node.dataset.articleId===wanted)
    if(card){card.classList.add('library-entry-highlight');card.scrollIntoView({block:'center'})}
  }
}

async function loadContext(){
  contextPayload=await jsonFetch('/api/context')
  const selected=current()
  const scopeParam=new URLSearchParams(location.search).get('scope')
  if($('#libraryScope'))$('#libraryScope').value=scopeParam==='workspace'?'workspace':selected.project_id?'project':'workspace'
  renderContext()
}

async function loadLibrary(){
  const state=$('#libraryStateMessage')
  const root=$('#libraryEntries')
  if(state)state.textContent='Carregando biblioteca…'
  if(root)root.innerHTML=''
  if(!current().workspace_id){if(state)state.textContent='Selecione um workspace.';return}
  renderContext()
  const scope=scopeValue()
  try{
    const payload=await jsonFetch(`/api/library?scope=${scope}&limit=500`)
    entriesCache=Array.isArray(payload.entries)?payload.entries:[]
    renderEntries()
    $('#libraryHealth').textContent=scope==='project'?'projeto atual':'workspace atual'
    $('#libraryHealth').classList.add('ok')
  }catch(error){
    entriesCache=[]
    if(state)state.textContent=error.status===409?'A base bibliográfica global ainda não está disponível neste ambiente.':error.status===403?'Seu papel não permite ver esta biblioteca.':'Não foi possível carregar a biblioteca.'
    if(root)root.innerHTML=''
    $('#libraryHealth').textContent='indisponível'
    $('#libraryHealth').classList.add('bad')
  }
}

async function savePlacement(){
  const status=$('#librarySaveStatus')
  const articleId=String($('#libraryArticleId')?.value||'').trim()
  if(!articleId){if(status)status.textContent='Informe o ID canônico do artigo.';return}
  const tags=String($('#libraryTags')?.value||'').split(',').map(value=>value.trim()).filter(Boolean)
  const body={article_id:articleId,scope:scopeValue(),state:$('#libraryState')?.value||'not_screened',tags,notes:String($('#libraryNotes')?.value||'')}
  if(status)status.textContent='Adicionando…'
  try{
    await jsonFetch('/api/library/placements',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
    if(status)status.textContent='Artigo adicionado à biblioteca deste contexto.'
    $('#libraryArticleId').value=''
    $('#libraryTags').value=''
    $('#libraryNotes').value=''
    await loadLibrary()
  }catch(error){
    if(status)status.textContent=error.status===404?'Esse ID não existe na base bibliográfica global.':error.status===403?'Seu papel não permite editar esta biblioteca.':'Não foi possível adicionar o artigo.'
  }
}

async function deletePlacement(id,button){
  if(!id)return
  if(button?.dataset.confirmDelete!=='true'){
    button.dataset.confirmDelete='true'
    button.textContent='Clique novamente para remover'
    setTimeout(()=>{if(button?.isConnected){delete button.dataset.confirmDelete;button.textContent='Remover da biblioteca'}},5000)
    return
  }
  button.disabled=true
  button.textContent='Removendo…'
  try{await jsonFetch(`/api/library/placements/${encodeURIComponent(id)}`,{method:'DELETE'});await loadLibrary()}
  catch{button.disabled=false;button.textContent='Tentar remover novamente'}
}

async function showFullText(articleId,button){
  if(!articleId)return
  const card=button.closest('[data-placement-id]')
  const target=card?.querySelector('[data-fulltext-status]')
  if(target)target.textContent='Verificando acesso…'
  try{
    const payload=await jsonFetch(`/api/library/full-text/${encodeURIComponent(articleId)}`)
    const grants=Array.isArray(payload.grants)?payload.grants:[]
    if(target)target.innerHTML=grants.length?grants.map(grant=>`<span>Acesso ${esc(grant.access_type||'disponível')} · redistribuição ${grant.redistribution_allowed?'permitida':'não permitida'}${grant.expires_at?` · expira em ${esc(new Date(grant.expires_at).toLocaleDateString('pt-BR'))}`:''}</span>`).join('<br>'):'Nenhum acesso ativo a texto completo neste contexto.'
  }catch{if(target)target.textContent='Texto completo não disponível para este contexto.'}
}

async function init(){
  const health=$('#libraryHealth')
  try{
    const auth=await jsonFetch('/api/auth/status')
    if(auth.mode!=='pilot'){
      if(health)health.textContent='modo legado'
      $('#libraryStateMessage').textContent='Esta biblioteca por workspace/projeto está disponível no modo autenticado.'
      return
    }
    await loadContext()
    await loadLibrary()
  }catch(error){
    if(error.status===401)return
    if(health)health.textContent='autenticação necessária'
    $('#libraryStateMessage').textContent='Entre no NutEV para acessar a biblioteca.'
  }
}

$('#libraryScope')?.addEventListener('change',()=>{const url=new URL(location.href);url.searchParams.set('scope',scopeValue());url.searchParams.delete('article');history.replaceState(null,'',url);loadLibrary()})
$('#libraryFilter')?.addEventListener('input',renderEntries)
$('#libraryStateFilter')?.addEventListener('change',renderEntries)
$('#refreshLibrary')?.addEventListener('click',loadLibrary)
$('#saveLibraryPlacement')?.addEventListener('click',savePlacement)
$('#libraryEntries')?.addEventListener('click',event=>{
  const deleteButton=event.target.closest('[data-delete-placement]')
  if(deleteButton){deletePlacement(deleteButton.dataset.deletePlacement,deleteButton);return}
  const fullTextButton=event.target.closest('[data-fulltext-article]')
  if(fullTextButton)showFullText(fullTextButton.dataset.fulltextArticle,fullTextButton)
})

init()
