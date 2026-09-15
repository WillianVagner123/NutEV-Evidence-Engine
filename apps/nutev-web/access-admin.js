import {accessT,applyAccessCopy} from './access-i18n.js'

const identity=document.querySelector('#adminIdentity')
const statusNode=document.querySelector('#adminStatus')
const filter=document.querySelector('#accessStatusFilter')
const refresh=document.querySelector('#refreshAccessRequests')
const list=document.querySelector('#accessRequestList')
const invitationOutput=document.querySelector('#invitationOutput')
const invitationLink=document.querySelector('#invitationLink')
const copyInvitationLink=document.querySelector('#copyInvitationLink')
let latestRequests=[]
let currentInvitation=''

function escapeHtml(value){
  return String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')
}

function locale(){return window.NutEVI18n?.language==='en'?'en-US':'pt-BR'}
function formatDate(value){if(!value)return'—';const d=new Date(value);return Number.isNaN(d.getTime())?'—':d.toLocaleString(locale())}
function statusLabel(value){
  return({
    pending:accessT('Pendente','Pending'),
    approved:accessT('Aprovada','Approved'),
    rejected:accessT('Rejeitada','Rejected'),
    accepted:accessT('Conta criada','Account created')
  })[value]||value
}

function setStatus(message,tone=''){
  statusNode.textContent=message
  statusNode.className=`access-status${tone?` ${tone}`:''}`
}

async function readJson(response){try{return await response.json()}catch{return{}}}

async function jsonFetch(url,options={}){
  const response=await fetch(url,{credentials:'same-origin',cache:'no-store',...options})
  const body=await readJson(response)
  if(!response.ok){
    const error=new Error(body?.message||body?.error||`HTTP ${response.status}`)
    error.status=response.status
    error.code=body?.error||''
    throw error
  }
  return body
}

function renderRequests(){
  if(!latestRequests.length){
    list.innerHTML=`<div class="access-empty">${escapeHtml(accessT('Nenhuma solicitação neste filtro.','No requests in this filter.'))}</div>`
    return
  }
  list.innerHTML=latestRequests.map(item=>{
    const canApprove=item.status==='pending'||item.status==='approved'
    const canReject=item.status==='pending'||item.status==='approved'
    const approveLabel=item.status==='approved'?accessT('Gerar novo link','Generate new link'):accessT('Aprovar e gerar link','Approve and generate link')
    const expiry=item.status==='approved'?(item.invitation_expired?accessT('Convite expirado','Invitation expired'):formatDate(item.invitation_expires_at)):'—'
    return`<article class="access-request-card" data-request-id="${escapeHtml(item.id)}">
      <div class="access-request-head">
        <div><h2>${escapeHtml(item.display_name)}</h2><p>${escapeHtml(item.email)}</p></div>
        <span class="access-status-badge ${escapeHtml(item.status)}">${escapeHtml(statusLabel(item.status))}</span>
      </div>
      <div class="access-request-meta">
        <div><span>${escapeHtml(accessT('Instituição','Institution'))}</span><strong>${escapeHtml(item.institution)}</strong></div>
        <div><span>${escapeHtml(accessT('Solicitada em','Requested'))}</span><strong>${escapeHtml(formatDate(item.created_at))}</strong></div>
        <div><span>${escapeHtml(accessT('Convite','Invitation'))}</span><strong>${escapeHtml(expiry)}</strong></div>
      </div>
      <p class="access-purpose">${escapeHtml(item.intended_use)}</p>
      ${item.rejection_reason?`<p class="access-purpose"><strong>${escapeHtml(accessT('Motivo da rejeição:','Rejection reason:'))}</strong> ${escapeHtml(item.rejection_reason)}</p>`:''}
      <div class="access-request-actions">
        ${canApprove?`<button class="access-action" type="button" data-approve="${escapeHtml(item.id)}">${escapeHtml(approveLabel)}</button>`:''}
      </div>
      ${canReject?`<details class="reject-box"><summary>${escapeHtml(accessT('Rejeitar solicitação','Reject request'))}</summary><textarea data-reject-reason="${escapeHtml(item.id)}" maxlength="500" placeholder="${escapeHtml(accessT('Motivo opcional para auditoria interna','Optional reason for internal audit'))}"></textarea><button class="access-action danger" type="button" data-reject="${escapeHtml(item.id)}">${escapeHtml(accessT('Confirmar rejeição','Confirm rejection'))}</button></details>`:''}
    </article>`
  }).join('')
}

async function loadRequests(){
  filter.disabled=true
  refresh.disabled=true
  setStatus(accessT('Carregando solicitações…','Loading requests…'))
  try{
    const payload=await jsonFetch(`/api/admin/access-requests?status=${encodeURIComponent(filter.value)}`)
    latestRequests=Array.isArray(payload.requests)?payload.requests:[]
    renderRequests()
    setStatus(accessT(`${latestRequests.length} solicitação(ões) exibida(s).`,`${latestRequests.length} request(s) shown.`),'success')
  }catch(error){
    if(error.status===401){location.replace(`/login.html?next=${encodeURIComponent('/access-admin.html')}`);return}
    if(error.status===403){setStatus(accessT('Esta conta não possui permissão de administração da plataforma.','This account does not have platform-administration permission.'),'error');return}
    setStatus(accessT('Não foi possível carregar as solicitações.','Could not load access requests.'),'error')
  }finally{
    filter.disabled=false
    refresh.disabled=false
    applyAccessCopy()
  }
}

async function approve(requestId,button){
  button.disabled=true
  setStatus(accessT('Gerando convite temporário…','Generating temporary invitation…'))
  try{
    const payload=await jsonFetch(`/api/admin/access-requests/${encodeURIComponent(requestId)}/approve`,{
      method:'POST',headers:{'Content-Type':'application/json'},body:'{}'
    })
    currentInvitation=new URL(payload.invitation_path,location.origin).href
    invitationLink.textContent=currentInvitation
    invitationOutput.classList.add('visible')
    setStatus(accessT('Solicitação aprovada. Copie o link e envie somente à pessoa aprovada.','Request approved. Copy the link and send it only to the approved person.'),'success')
    await loadRequests()
  }catch(error){
    setStatus(error.status===409?accessT('Esta solicitação não pode mais ser aprovada neste estado.','This request can no longer be approved in its current state.'):accessT('Não foi possível aprovar a solicitação.','Could not approve the request.'),'error')
  }finally{button.disabled=false}
}

async function reject(requestId,button){
  const textarea=document.querySelector(`[data-reject-reason="${CSS.escape(requestId)}"]`)
  const reason=String(textarea?.value||'').trim()
  button.disabled=true
  setStatus(accessT('Registrando rejeição…','Recording rejection…'))
  try{
    await jsonFetch(`/api/admin/access-requests/${encodeURIComponent(requestId)}/reject`,{
      method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reason})
    })
    setStatus(accessT('Solicitação rejeitada.','Request rejected.'),'success')
    await loadRequests()
  }catch{
    setStatus(accessT('Não foi possível rejeitar a solicitação.','Could not reject the request.'),'error')
  }finally{button.disabled=false}
}

list?.addEventListener('click',event=>{
  const approveButton=event.target.closest('[data-approve]')
  if(approveButton){approve(approveButton.dataset.approve,approveButton);return}
  const rejectButton=event.target.closest('[data-reject]')
  if(rejectButton)reject(rejectButton.dataset.reject,rejectButton)
})

copyInvitationLink?.addEventListener('click',async()=>{
  if(!currentInvitation)return
  try{
    await navigator.clipboard.writeText(currentInvitation)
    setStatus(accessT('Link copiado.','Link copied.'),'success')
  }catch{
    setStatus(accessT('Não foi possível copiar automaticamente. Selecione o link acima e copie manualmente.','Could not copy automatically. Select the link above and copy it manually.'),'error')
  }
})

filter?.addEventListener('change',loadRequests)
refresh?.addEventListener('click',loadRequests)
window.addEventListener('nutev:language-change',()=>{applyAccessCopy();renderRequests()})

async function init(){
  try{
    const me=await fetch('/api/auth/me',{credentials:'same-origin',cache:'no-store'})
    if(me.status===401){location.replace(`/login.html?next=${encodeURIComponent('/access-admin.html')}`);return}
    const payload=await readJson(me)
    if(!me.ok)throw new Error('auth_unavailable')
    if(!Array.isArray(payload.global_roles)||!payload.global_roles.includes('PLATFORM_ADMIN')){
      identity.textContent=payload?.user?.display_name||accessT('Conta autenticada','Authenticated account')
      setStatus(accessT('Apenas administradores da plataforma podem revisar solicitações de acesso.','Only platform administrators can review access requests.'),'error')
      list.innerHTML=''
      return
    }
    identity.textContent=accessT(`Administrador: ${payload.user?.display_name||'—'}`,`Administrator: ${payload.user?.display_name||'—'}`)
    filter.disabled=false
    refresh.disabled=false
    await loadRequests()
  }catch{
    setStatus(accessT('Não foi possível validar a sessão administrativa.','Could not validate the administrative session.'),'error')
    list.innerHTML=''
  }
}

init()
