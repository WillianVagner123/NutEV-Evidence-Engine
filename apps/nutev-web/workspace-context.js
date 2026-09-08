const state={loading:false,rendered:false}
const PROTECTED_PILOT_PATHS=new Set(['/search.html','/evidence-library.html','/project.html','/exports.html'])

function esc(value){
  return String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')
}

async function jsonFetch(url,options={}){
  const response=await fetch(url,{cache:'no-store',credentials:'same-origin',...options})
  let payload={}
  try{payload=await response.json()}catch{}
  if(!response.ok){
    const error=new Error(String(payload?.error||`http_${response.status}`))
    error.status=response.status
    error.payload=payload
    throw error
  }
  return payload
}

function optionHtml(items,current,emptyLabel){
  const empty=`<option value="">${esc(emptyLabel)}</option>`
  const rows=items.map(item=>`<option value="${esc(item.id)}"${item.id===current?' selected':''}>${esc(item.name)}</option>`).join('')
  return empty+rows
}

function nextLoginUrl(){
  const next=`${location.pathname}${location.search}${location.hash}`
  return `/login.html?next=${encodeURIComponent(next)}`
}

function hostAndTopbar(){
  const host=document.querySelector('main.main,.main,.workspace,.workspace-body')
  return{host,topbar:host?.querySelector('.topbar,header')||null}
}

function insertAfterTopbar(root){
  const {host,topbar}=hostAndTopbar()
  if(!host)return false
  if(topbar)topbar.insertAdjacentElement('afterend',root)
  else host.prepend(root)
  return true
}

function renderSignedOut(){
  if(document.querySelector('#nutevWorkspaceProjectSwitcher'))return
  if(PROTECTED_PILOT_PATHS.has(location.pathname)){
    location.replace(nextLoginUrl())
    return
  }
  const root=document.createElement('section')
  root.id='nutevWorkspaceProjectSwitcher'
  root.className='context-shell context-shell-signed-out'
  root.setAttribute('aria-label','Sessão do NutEV')
  root.innerHTML=`<div class="context-summary"><span class="context-kicker">NutEV autenticado</span><strong>Entre para acessar seus workspaces e projetos.</strong></div><a class="context-login" href="${esc(nextLoginUrl())}">Entrar</a>`
  insertAfterTopbar(root)
}

function roleLabel(value){
  const labels={
    WORKSPACE_OWNER:'Proprietário',
    WORKSPACE_ADMIN:'Administrador',
    RESEARCHER:'Pesquisador',
    REVIEWER:'Revisor',
    VIEWER:'Visualizador',
    GUEST_REVIEWER:'Revisor convidado',
    PLATFORM_ADMIN:'Admin da plataforma'
  }
  return labels[String(value||'')]||String(value||'')
}

function currentNames(context){
  const current=context.current||{}
  const workspace=(context.workspaces||[]).find(item=>item.id===current.workspace_id)||null
  const project=(context.projects||[]).find(item=>item.id===current.project_id)||null
  return{workspace,project}
}

async function selectContext(workspaceId,projectId){
  await jsonFetch('/api/context/select',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({workspace_id:workspaceId||null,project_id:projectId||null})
  })
  location.reload()
}

async function logout(button){
  if(button)button.disabled=true
  try{await jsonFetch('/api/auth/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})}catch{}
  location.replace('/login.html')
}

function currentMembership(me,workspaceId){
  return (me.workspace_memberships||[]).find(item=>item.workspace_id===workspaceId)||null
}

function renderContextShell(me,context){
  document.querySelector('#nutevWorkspaceProjectSwitcher')?.remove()
  const workspaces=Array.isArray(context.workspaces)?context.workspaces:[]
  const projects=Array.isArray(context.projects)?context.projects:[]
  const current=context.current||{}
  const names=currentNames(context)
  const membership=currentMembership(me,current.workspace_id)
  const root=document.createElement('section')
  root.id='nutevWorkspaceProjectSwitcher'
  root.className='context-shell'
  root.setAttribute('aria-label','Contexto de pesquisa atual')
  root.innerHTML=`
    <div class="context-fields">
      <label><span>Workspace</span>
        <select id="nutevWorkspaceSelect" aria-label="Selecionar workspace">
          ${optionHtml(workspaces,current.workspace_id,'Selecionar workspace')}
        </select>
      </label>
      <span class="context-separator" aria-hidden="true">/</span>
      <label><span>Projeto</span>
        <select id="nutevProjectSelect" aria-label="Selecionar projeto" ${current.workspace_id?'':'disabled'}>
          ${optionHtml(projects,current.project_id,'Selecionar projeto')}
        </select>
      </label>
      ${current.project_id?'<a class="context-project-link" href="/project.html">Abrir projeto</a>':''}
    </div>
    <div class="context-account">
      <div class="context-account-copy"><strong>${esc(me.user?.display_name||'Usuário')}</strong><span>${membership?esc(roleLabel(membership.role)):'Sessão autenticada'}</span></div>
      <button class="context-logout" id="nutevLogoutButton" type="button">Sair</button>
    </div>`
  if(!insertAfterTopbar(root))return

  const workspaceSelect=root.querySelector('#nutevWorkspaceSelect')
  const projectSelect=root.querySelector('#nutevProjectSelect')
  workspaceSelect?.addEventListener('change',async event=>{
    workspaceSelect.disabled=true
    if(projectSelect)projectSelect.disabled=true
    try{await selectContext(event.target.value||null,null)}catch(error){
      root.dataset.error=String(error.message||'context_error')
      location.reload()
    }
  })
  projectSelect?.addEventListener('change',async event=>{
    if(!workspaceSelect?.value)return
    projectSelect.disabled=true
    try{await selectContext(workspaceSelect.value,event.target.value||null)}catch(error){
      root.dataset.error=String(error.message||'context_error')
      location.reload()
    }
  })
  root.querySelector('#nutevLogoutButton')?.addEventListener('click',event=>logout(event.currentTarget))

  document.body.dataset.nutevWorkspace=current.workspace_id||''
  document.body.dataset.nutevProject=current.project_id||''
  window.NutEVContext={mode:'pilot',me,context,names}
  window.dispatchEvent(new CustomEvent('nutev:context-ready',{detail:window.NutEVContext}))
}

function renderContextError(message='Não foi possível carregar o contexto de pesquisa.'){
  document.querySelector('#nutevWorkspaceProjectSwitcher')?.remove()
  const root=document.createElement('section')
  root.id='nutevWorkspaceProjectSwitcher'
  root.className='context-shell context-shell-error'
  root.setAttribute('role','alert')
  root.innerHTML=`<div><strong>Contexto indisponível</strong><span>${esc(message)}</span></div><button class="context-retry" type="button">Tentar novamente</button>`
  if(!insertAfterTopbar(root))return
  root.querySelector('.context-retry')?.addEventListener('click',()=>{root.remove();state.rendered=false;renderWorkspaceProjectSwitcher()})
}

export async function renderWorkspaceProjectSwitcher(){
  if(state.loading||state.rendered||location.pathname==='/login.html')return
  state.loading=true
  try{
    const status=await jsonFetch('/api/auth/status')
    if(status.mode!=='pilot')return
    let me
    try{me=await jsonFetch('/api/auth/me')}
    catch(error){
      if(error.status===401){renderSignedOut();state.rendered=true;return}
      throw error
    }
    const context=await jsonFetch('/api/context')
    renderContextShell(me,context)
    state.rendered=true
  }catch(error){
    if(error.status===401){renderSignedOut();state.rendered=true}
    else renderContextError(error.status===503?'Serviço de contexto temporariamente indisponível.':'Não foi possível carregar sua sessão e seus projetos.')
  }finally{
    state.loading=false
  }
}

renderWorkspaceProjectSwitcher()
