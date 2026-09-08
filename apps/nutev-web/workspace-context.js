const state={loading:false}

function esc(value){
  return String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')
}

async function jsonFetch(url,options={}){
  const response=await fetch(url,{cache:'no-store',credentials:'same-origin',...options})
  if(!response.ok)throw new Error(`http_${response.status}`)
  return response.json()
}

function optionHtml(items,current,emptyLabel){
  const empty=`<option value="">${esc(emptyLabel)}</option>`
  const rows=items.map(item=>`<option value="${esc(item.id)}"${item.id===current?' selected':''}>${esc(item.name)}</option>`).join('')
  return empty+rows
}

async function selectContext(workspaceId,projectId){
  await jsonFetch('/api/context/select',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({workspace_id:workspaceId||null,project_id:projectId||null})
  })
  location.reload()
}

function styleSwitcher(root){
  root.style.display='flex'
  root.style.flexWrap='wrap'
  root.style.alignItems='end'
  root.style.gap='.55rem'
  root.style.padding='.65rem .8rem'
  root.style.margin='0 0 .8rem'
  root.style.border='1px solid var(--border,#d9e0e7)'
  root.style.borderRadius='12px'
  root.style.background='var(--surface,#fff)'
  root.querySelectorAll('label').forEach(label=>{
    label.style.display='grid'
    label.style.gap='.2rem'
    label.style.fontSize='.76rem'
    label.style.fontWeight='700'
  })
  root.querySelectorAll('select').forEach(select=>{
    select.style.minWidth='180px'
    select.style.maxWidth='280px'
    select.style.padding='.45rem .55rem'
  })
}

export async function renderWorkspaceProjectSwitcher(){
  if(state.loading||document.querySelector('#nutevWorkspaceProjectSwitcher'))return
  state.loading=true
  try{
    const status=await jsonFetch('/api/auth/status')
    if(status.mode!=='pilot')return
    const context=await jsonFetch('/api/context')
    const workspaces=Array.isArray(context.workspaces)?context.workspaces:[]
    if(!workspaces.length)return
    const projects=Array.isArray(context.projects)?context.projects:[]
    const current=context.current||{}
    const host=document.querySelector('main.main,.main,.workspace,.workspace-body')
    if(!host)return
    const topbar=host.querySelector('.topbar,header')
    const root=document.createElement('section')
    root.id='nutevWorkspaceProjectSwitcher'
    root.setAttribute('aria-label','Contexto de pesquisa atual')
    root.innerHTML=`
      <label>Workspace
        <select id="nutevWorkspaceSelect" aria-label="Selecionar workspace">
          ${optionHtml(workspaces,current.workspace_id,'Selecionar workspace')}
        </select>
      </label>
      <label>Projeto
        <select id="nutevProjectSelect" aria-label="Selecionar projeto" ${current.workspace_id?'':'disabled'}>
          ${optionHtml(projects,current.project_id,'Biblioteca do workspace')}
        </select>
      </label>
      <span style="font-size:.75rem;max-width:310px;opacity:.7">Contexto da sessão. A seleção não concede permissão; cada operação privada é revalidada no backend.</span>`
    styleSwitcher(root)
    if(topbar)topbar.insertAdjacentElement('afterend',root)
    else host.prepend(root)

    const workspaceSelect=root.querySelector('#nutevWorkspaceSelect')
    const projectSelect=root.querySelector('#nutevProjectSelect')
    workspaceSelect?.addEventListener('change',async event=>{
      workspaceSelect.disabled=true
      if(projectSelect)projectSelect.disabled=true
      try{await selectContext(event.target.value||null,null)}catch{location.reload()}
    })
    projectSelect?.addEventListener('change',async event=>{
      if(!workspaceSelect?.value)return
      projectSelect.disabled=true
      try{await selectContext(workspaceSelect.value,event.target.value||null)}catch{location.reload()}
    })
  }catch{
    // Auth may be disabled or the user may not have an authenticated pilot session.
    // In either case the legacy product UI remains untouched.
  }finally{
    state.loading=false
  }
}

renderWorkspaceProjectSwitcher()
