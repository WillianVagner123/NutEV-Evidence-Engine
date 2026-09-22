const $=selector=>document.querySelector(selector)
const esc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')

const ROLE_LABELS={
  WORKSPACE_OWNER:'Proprietário',
  WORKSPACE_ADMIN:'Administrador',
  RESEARCHER:'Pesquisador',
  REVIEWER:'Revisor',
  VIEWER:'Visualizador',
  ACADEMIC_SUPERVISOR:'Professor orientador',
  GUEST_REVIEWER:'Revisor convidado'
}
const ROLE_HELP={
  WORKSPACE_ADMIN:'Administra o workspace, os membros e todo o trabalho dos projetos.',
  RESEARCHER:'Trabalha nos projetos: busca, biblioteca, triagem e extração.',
  REVIEWER:'Apenas triagem e extração dos registros atribuídos a essa pessoa.',
  VIEWER:'Leitura dos projetos do workspace, sem escrita.',
  ACADEMIC_SUPERVISOR:'Leitura dos projetos e da trilha de auditoria. Não executa busca, triagem, extração nem adjudicação, e não gerencia membros. Acompanhar não é aprovar.',
  GUEST_REVIEWER:'Revisor externo, restrito ao que lhe for atribuído.'
}
const STATUS_LABELS={active:'Ativo',invited:'Convidado',suspended:'Suspenso',removed:'Removido'}

async function jsonFetch(url,options={}){
  const response=await fetch(url,{cache:'no-store',credentials:'same-origin',...options})
  let payload={}
  try{payload=await response.json()}catch{}
  if(!response.ok){const error=new Error(payload?.error||`http_${response.status}`);error.status=response.status;error.payload=payload;throw error}
  return payload
}

function roleLabel(value){return ROLE_LABELS[String(value||'')]||String(value||'')}
function statusLabel(value){return STATUS_LABELS[String(value||'')]||String(value||'')}

function renderUnavailable(title,copy,health){
  $('#membersHealth').textContent=health
  $('#membersState').innerHTML=`<div class="empty-state"><strong>${esc(title)}</strong><span>${esc(copy)}</span></div>`
  $('#grantPanel').classList.add('hidden')
  $('#rosterPanel').classList.add('hidden')
}

function renderRoles(roles){
  const select=$('#grantRole')
  const preferred=roles.includes('ACADEMIC_SUPERVISOR')?'ACADEMIC_SUPERVISOR':roles[0]
  select.innerHTML=roles.map(role=>`<option value="${esc(role)}"${role===preferred?' selected':''}>${esc(roleLabel(role))}</option>`).join('')
  updateRoleHelp()
}

function updateRoleHelp(){
  const role=$('#grantRole')?.value||''
  $('#roleHelp').textContent=ROLE_HELP[role]||''
}

function memberRow(member){
  const name=member.display_name||member.email||'Membro'
  const badges=[
    member.is_workspace_owner?'<span class="project-badge">Proprietário do workspace</span>':'',
    member.is_current_user?'<span class="project-badge neutral">Você</span>':''
  ].join('')
  // The owner's role and status are not editable anywhere, so the controls are simply not
  // rendered rather than rendered and refused by the server on click.
  const controls=member.status_editable
    ? `<div class="member-actions">
         <button class="action-secondary" type="button" data-action="suspend" data-user="${esc(member.user_id)}"${member.status==='suspended'?' disabled':''}>Suspender</button>
         <button class="action-secondary" type="button" data-action="restore" data-user="${esc(member.user_id)}"${member.status==='active'?' disabled':''}>Reativar</button>
         <button class="action-secondary" type="button" data-action="remove" data-user="${esc(member.user_id)}"${member.status==='removed'?' disabled':''}>Remover</button>
       </div>`
    : '<div class="member-actions"><span class="small-state">A propriedade do workspace não muda por esta tela.</span></div>'
  return `<div class="member-row" data-member="${esc(member.user_id)}">
    <div class="member-identity"><strong>${esc(name)}</strong><span>${esc(member.email||'')}</span></div>
    <div class="member-role"><span class="component-chip">${esc(roleLabel(member.role))}</span><span class="small-state">${esc(statusLabel(member.status))}</span>${badges}</div>
    ${controls}
  </div>`
}

function renderRoster(payload){
  $('#membersHealth').textContent='acesso do workspace'
  $('#membersState').innerHTML=`<div class="product-panel-head"><div class="project-identity"><div class="project-mark" aria-hidden="true">◇</div><div class="project-identity-copy"><strong>${esc(payload.workspace?.name||'Workspace')}</strong><span>${payload.members.length} pessoa(s) com acesso registrado</span></div></div><a class="action-secondary" href="/project.html">Voltar ao projeto</a></div>`
  $('#roster').innerHTML=payload.members.map(memberRow).join('')
  $('#rosterPanel').classList.remove('hidden')
  $('#grantPanel').classList.remove('hidden')
}

async function load(){
  const payload=await jsonFetch('/api/workspace/members')
  renderRoles(Array.isArray(payload.assignable_roles)?payload.assignable_roles:[])
  renderRoster(payload)
  return payload
}

function grantError(error){
  if(error.status===403)return 'Seu papel não permite gerenciar membros deste workspace.'
  if(error.status===404)return 'Nenhuma conta ativa com esse e-mail. A pessoa precisa concluir o convite e definir a senha antes de receber acesso.'
  if(error.status===409&&error.payload?.error==='ownership_transfer_not_supported_here')return 'A propriedade do workspace não muda por esta tela.'
  if(error.status===409)return 'Não foi possível concluir. Atualize a página e confira o estado atual.'
  if(error.status===400)return 'Papel inválido para este workspace.'
  return 'Não foi possível conceder o acesso.'
}

async function submitGrant(event){
  event.preventDefault()
  const button=$('#grantSubmit')
  const status=$('#grantStatus')
  const email=$('#grantEmail').value.trim()
  const role=$('#grantRole').value
  if(!email){status.textContent='Informe o e-mail da pessoa.';return}
  button.disabled=true
  status.textContent='Concedendo acesso…'
  try{
    await jsonFetch('/api/workspace/members',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,role})})
    status.textContent='Acesso concedido.'
    $('#grantEmail').value=''
    await load()
  }catch(error){
    if(error.status===409&&error.payload?.error==='role_change_requires_explicit_confirmation'){
      const from=roleLabel(error.payload.current_role)
      const to=roleLabel(error.payload.requested_role)
      if(window.confirm(`Esta pessoa já tem acesso como ${from}. Alterar para ${to}?`)){
        try{
          await jsonFetch('/api/workspace/members',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,role,allow_role_change:true})})
          status.textContent='Papel alterado.'
          $('#grantEmail').value=''
          await load()
        }catch(inner){status.textContent=grantError(inner)}
      }else{
        status.textContent='Nada foi alterado.'
      }
    }else{
      status.textContent=grantError(error)
    }
  }finally{
    button.disabled=false
  }
}

const STATUS_BY_ACTION={suspend:'suspended',restore:'active',remove:'removed'}
const CONFIRM_BY_ACTION={
  suspend:'Suspender o acesso desta pessoa ao workspace?',
  remove:'Remover o acesso desta pessoa ao workspace?'
}

async function changeStatus(event){
  const button=event.target.closest('button[data-action]')
  if(!button)return
  const action=button.dataset.action
  const status=STATUS_BY_ACTION[action]
  if(!status)return
  const question=CONFIRM_BY_ACTION[action]
  if(question&&!window.confirm(question))return
  button.disabled=true
  try{
    await jsonFetch('/api/workspace/members/status',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:button.dataset.user,status})})
    await load()
  }catch(error){
    $('#grantStatus').textContent=error.status===403
      ?'Seu papel não permite gerenciar membros deste workspace.'
      :error.status===409?'A propriedade do workspace não muda por esta tela.':'Não foi possível atualizar este acesso.'
    button.disabled=false
  }
}

async function init(){
  try{
    const auth=await jsonFetch('/api/auth/status')
    if(auth.mode!=='pilot'){
      renderUnavailable('Gestão de membros indisponível neste runtime','O modo legado mantém a experiência local. Workspaces e membros ficam disponíveis no modo autenticado.','modo legado')
      return
    }
    await load()
  }catch(error){
    if(error.status===401)return
    if(error.status===403){
      renderUnavailable('Você não gerencia os membros deste workspace','Somente o proprietário ou um administrador do workspace pode ver e alterar quem tem acesso.','acesso restrito')
      return
    }
    if(error.status===409){
      renderUnavailable('Selecione um workspace','Use o seletor de contexto acima para escolher o workspace antes de gerenciar o acesso.','workspace necessário')
      return
    }
    renderUnavailable('Não foi possível carregar os membros','O contexto ou o serviço de membros está temporariamente indisponível.','indisponível')
  }
}

$('#grantForm')?.addEventListener('submit',submitGrant)
$('#grantRole')?.addEventListener('change',updateRoleHelp)
$('#roster')?.addEventListener('click',changeStatus)
init()
