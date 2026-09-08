const panel=document.querySelector('#homeWorkspacePanel')
const runtimeStatus=document.querySelector('#homeRuntimeStatus')
const libraryLinks=[...document.querySelectorAll('[data-library-link]')]
const pilotOnly=[...document.querySelectorAll('[data-pilot-only]')]
const esc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')

async function jsonFetch(url,options={}){
  const response=await fetch(url,{cache:'no-store',credentials:'same-origin',...options})
  let payload={}
  try{payload=await response.json()}catch{}
  if(!response.ok){const error=new Error(payload?.error||`http_${response.status}`);error.status=response.status;throw error}
  return payload
}

function appLabel(value){
  const labels={GENERIC_EVIDENCE_PROJECT:'Projeto de evidências',SCOPING_REVIEW:'Revisão de escopo',INTEGRATIVE_REVIEW:'Revisão integrativa'}
  return labels[String(value||'')]||'Aplicação ainda não configurada'
}
function nameFor(items,id){return(items||[]).find(item=>item.id===id)?.name||''}

async function selectProject(workspaceId,projectId,button){
  button.disabled=true
  button.textContent='Abrindo…'
  try{
    await jsonFetch('/api/context/select',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({workspace_id:workspaceId,project_id:projectId})})
    location.href='/project.html'
  }catch{button.disabled=false;button.textContent='Abrir projeto'}
}

function renderSignedOut(){
  runtimeStatus.textContent='login necessário'
  panel.innerHTML='<div class="product-panel-head"><div><span class="home-eyebrow">Seu espaço de pesquisa</span><h2>Entre para acessar workspaces e projetos</h2><p>Busca privada, biblioteca, histórico e exportações são isolados pela sessão autenticada.</p></div></div><div class="product-actions"><a class="action-primary" href="/login.html">Entrar no NutEV</a></div>'
}

function renderProjectChooser(me,context){
  const projects=Array.isArray(context.projects)?context.projects:[]
  const current=context.current||{}
  const workspaceName=nameFor(context.workspaces,current.workspace_id)||'Seu workspace'
  runtimeStatus.textContent='workspace selecionado'
  panel.innerHTML=`<div class="product-panel-head"><div><span class="home-eyebrow">Olá, ${esc(me.user?.display_name||'pesquisador')}</span><h2>${esc(workspaceName)}</h2><p>Selecione um projeto para ativar o contexto de busca, biblioteca e exportação.</p></div><span class="project-badge neutral">${projects.length.toLocaleString('pt-BR')} projeto(s)</span></div>${projects.length?`<div class="module-grid">${projects.map(project=>`<article class="module-card"><span class="module-icon" aria-hidden="true">◇</span><strong>${esc(project.name)}</strong><span>${esc(project.project_type||'Projeto de pesquisa')}</span><div class="module-meta"><button class="ghost" type="button" data-open-project="${esc(project.id)}" data-workspace-id="${esc(project.workspace_id)}">Abrir projeto</button></div></article>`).join('')}</div>`:'<div class="empty-state"><strong>Nenhum projeto disponível</strong><span>Seu workspace está acessível, mas não há projeto visível para esta conta.</span></div>'}`
  panel.querySelectorAll('[data-open-project]').forEach(button=>button.addEventListener('click',()=>selectProject(button.dataset.workspaceId,button.dataset.openProject,button)))
}

function renderCurrentProject(me,context,application){
  const current=context.current||{}
  const workspaceName=nameFor(context.workspaces,current.workspace_id)||'Workspace'
  const projectName=nameFor(context.projects,current.project_id)||'Projeto'
  const label=appLabel(application?.application_type)
  runtimeStatus.textContent='contexto autenticado'
  runtimeStatus.classList.add('ok')
  panel.innerHTML=`<div class="product-panel-head"><div class="project-identity"><div class="project-mark" aria-hidden="true">◇</div><div class="project-identity-copy"><span class="home-eyebrow">Olá, ${esc(me.user?.display_name||'pesquisador')}</span><strong>${esc(projectName)}</strong><span>${esc(workspaceName)} · ${esc(label)}</span></div></div><span class="project-badge ${application?'':'neutral'}">${application?'Projeto pronto':'Configuração pendente'}</span></div><div class="product-actions"><a class="action-primary" href="/project.html">Abrir projeto</a><a class="action-secondary" href="/search.html">Buscar evidências</a><a class="action-secondary" href="/evidence-library.html">Biblioteca</a><a class="action-secondary" href="/exports.html">Exportações</a></div>`
}

async function init(){
  try{
    const status=await jsonFetch('/api/auth/status')
    if(status.mode!=='pilot'){
      runtimeStatus.textContent='modo legado'
      libraryLinks.forEach(link=>link.href='/articles.html')
      pilotOnly.forEach(node=>node.classList.add('hidden'))
      panel.innerHTML='<div class="product-panel-head"><div><span class="home-eyebrow">Modo local</span><h2>NutEV em compatibilidade legada</h2><p>Este runtime usa sessão local do navegador. Workspaces, projetos e login de plataforma não estão ativos aqui.</p></div><span class="project-badge neutral">Legacy</span></div>'
      return
    }
    libraryLinks.forEach(link=>link.href='/evidence-library.html')
    let me
    try{me=await jsonFetch('/api/auth/me')}catch(error){if(error.status===401){renderSignedOut();return}throw error}
    const context=await jsonFetch('/api/context')
    if(!context.current?.project_id){renderProjectChooser(me,context);return}
    let application=null
    try{application=(await jsonFetch('/api/application')).application||null}catch(error){if(error.status!==404)throw error}
    renderCurrentProject(me,context,application)
  }catch{
    runtimeStatus.textContent='contexto indisponível'
    panel.innerHTML='<div class="empty-state"><strong>Não foi possível carregar seu contexto</strong><span>O motor continua protegido; atualize a página para tentar novamente.</span></div>'
  }
}

init()
