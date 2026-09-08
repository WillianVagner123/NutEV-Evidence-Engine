const $=selector=>document.querySelector(selector)
const esc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')
let exportsCache=[]

async function jsonFetch(url,options={}){
  const response=await fetch(url,{cache:'no-store',credentials:'same-origin',...options})
  let payload={}
  try{payload=await response.json()}catch{}
  if(!response.ok){const error=new Error(payload?.error||`http_${response.status}`);error.status=response.status;throw error}
  return payload
}

function nameFor(items,id){return(items||[]).find(item=>item.id===id)?.name||''}
function humanToken(value){return String(value||'').replaceAll('_',' ').replaceAll('-',' ').trim().replace(/\b\w/g,char=>char.toLocaleUpperCase('pt-BR'))||'Exportação'}
function formatBytes(value){
  const bytes=Number(value||0)
  if(!Number.isFinite(bytes)||bytes<=0)return'0 B'
  const units=['B','KB','MB','GB'];let size=bytes,index=0
  while(size>=1024&&index<units.length-1){size/=1024;index+=1}
  return`${size>=10||index===0?Math.round(size):size.toFixed(1)} ${units[index]}`
}
function formatDate(value){
  if(!value)return'—'
  const date=new Date(value)
  if(Number.isNaN(date.getTime()))return String(value)
  return new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(date)
}

function hideTenantSections(){
  $('#auditSummarySection').classList.add('hidden')
  $('#exportsSection').classList.add('hidden')
  $('#auditSection').classList.add('hidden')
}

function renderLegacy(){
  $('#exportsHealth').textContent='modo legado'
  $('#exportsContext').innerHTML='<div class="empty-state"><strong>Exportações multi-tenant não estão ativas neste runtime</strong><span>O modo legado mantém a experiência local. Manifestos e auditoria por projeto ficam disponíveis no modo autenticado.</span></div>'
  hideTenantSections()
}

function renderContext(context){
  const current=context.current||{}
  if(!current.project_id){
    $('#exportsHealth').textContent='projeto necessário'
    $('#exportsContext').innerHTML='<div class="empty-state"><strong>Selecione um projeto</strong><span>Exportações e auditoria são sempre consultadas dentro de um projeto explícito.</span></div>'
    hideTenantSections()
    return false
  }
  const workspaceName=nameFor(context.workspaces,current.workspace_id)||'Workspace'
  const projectName=nameFor(context.projects,current.project_id)||'Projeto'
  $('#exportsContext').innerHTML=`<div class="project-identity"><div class="project-mark" aria-hidden="true">⇩</div><div class="project-identity-copy"><strong>${esc(projectName)}</strong><span>${esc(workspaceName)} · exportações privadas deste projeto</span></div></div>`
  return true
}

function renderExportCards(exports){
  const root=$('#exportList')
  if(!exports.length){root.innerHTML='<div class="empty-state"><strong>Nenhuma exportação registrada</strong><span>Quando um fluxo do projeto gerar um pacote canônico, ele aparecerá aqui com manifesto e hashes.</span></div>';return}
  root.innerHTML=exports.map(item=>`<article class="export-card" data-export-id="${esc(item.id)}"><div class="export-head"><div><strong>${esc(humanToken(item.export_kind))}</strong><div class="export-meta">${esc(formatDate(item.created_at))} · ${Number(item.artifact_count||0).toLocaleString('pt-BR')} arquivo(s) · ${esc(formatBytes(item.total_bytes))}</div></div><span class="project-badge neutral">Manifesto ${esc(String(item.manifest_sha256||'').slice(0,12)||'—')}</span></div><div class="product-actions"><button class="action-secondary" type="button" data-manifest="${esc(item.id)}">Ver manifesto</button></div><div class="export-manifest hidden" data-manifest-panel></div></article>`).join('')
}

function renderAudit(audit){
  const chainValid=Boolean(audit.chain_valid)
  const events=Array.isArray(audit.events)?audit.events:[]
  $('#auditChainValue').textContent=chainValid?'Íntegra':'Falha'
  $('#auditChainKpi').classList.toggle('ok',chainValid)
  $('#auditChainKpi').classList.toggle('bad',!chainValid)
  $('#auditEventCount').textContent=events.length.toLocaleString('pt-BR')
  const root=$('#auditEvents')
  if(!events.length){root.innerHTML='<div class="empty-state"><strong>Sem eventos neste recorte</strong><span>A trilha será preenchida conforme ações auditáveis ocorrerem no projeto.</span></div>';return}
  root.innerHTML=events.map(event=>`<div class="audit-event"><time datetime="${esc(event.created_at||'')}">${esc(formatDate(event.created_at))}</time><div><strong>${esc(humanToken(event.event_type))}</strong><div class="export-meta">${esc(humanToken(event.resource_type))}${event.resource_id?` · ${esc(String(event.resource_id).slice(0,18))}`:''}</div>${event.details&&Object.keys(event.details).length?`<details class="advanced-id-entry"><summary>Detalhes do evento</summary><code>${esc(JSON.stringify(event.details,null,2))}</code></details>`:''}</div></div>`).join('')
}

async function showManifest(exportId,button){
  const card=button.closest('[data-export-id]')
  const panel=card?.querySelector('[data-manifest-panel]')
  if(!panel)return
  if(!panel.classList.contains('hidden')){panel.classList.add('hidden');button.textContent='Ver manifesto';return}
  button.disabled=true
  panel.classList.remove('hidden')
  panel.innerHTML='<span class="small-state">Carregando manifesto…</span>'
  try{
    const payload=await jsonFetch(`/api/exports/${encodeURIComponent(exportId)}/manifest`)
    const manifest=payload.manifest||{}
    const artifacts=Array.isArray(manifest.artifacts)?manifest.artifacts:[]
    panel.innerHTML=`<strong>Arquivos verificados</strong>${artifacts.length?`<div class="export-artifacts">${artifacts.map(artifact=>`<a href="/api/exports/${encodeURIComponent(exportId)}/artifacts/${encodeURIComponent(artifact.name)}">${esc(artifact.name)} · ${esc(formatBytes(artifact.size_bytes))}</a>`).join('')}</div>`:'<div class="export-meta">O manifesto não lista artefatos.</div>'}<details class="advanced-id-entry"><summary>Manifesto técnico</summary><code>${esc(JSON.stringify(manifest,null,2))}</code></details>`
    button.textContent='Ocultar manifesto'
  }catch{
    panel.innerHTML='<span class="small-state">Não foi possível carregar o manifesto deste projeto.</span>'
  }finally{button.disabled=false}
}

async function loadAll(){
  $('#exportsHealth').textContent='carregando…'
  try{
    const auth=await jsonFetch('/api/auth/status')
    if(auth.mode!=='pilot'){renderLegacy();return}
    const context=await jsonFetch('/api/context')
    if(!renderContext(context))return
    const [exportsPayload,auditPayload]=await Promise.all([jsonFetch('/api/exports'),jsonFetch('/api/audit?limit=50')])
    exportsCache=Array.isArray(exportsPayload.exports)?exportsPayload.exports:[]
    renderExportCards(exportsCache)
    renderAudit(auditPayload)
    $('#exportCount').textContent=exportsCache.length.toLocaleString('pt-BR')
    $('#auditSummarySection').classList.remove('hidden')
    $('#exportsSection').classList.remove('hidden')
    $('#auditSection').classList.remove('hidden')
    $('#exportsHealth').textContent=auditPayload.chain_valid?'auditoria íntegra':'auditoria requer atenção'
    $('#exportsHealth').classList.toggle('ok',Boolean(auditPayload.chain_valid))
    $('#exportsHealth').classList.toggle('bad',!auditPayload.chain_valid)
  }catch(error){
    if(error.status===401)return
    $('#exportsHealth').textContent='indisponível'
    $('#exportsContext').innerHTML=`<div class="empty-state"><strong>Não foi possível carregar exportações</strong><span>${error.status===403?'Seu papel não permite acessar exportações ou auditoria deste projeto.':'O serviço de exportações está temporariamente indisponível.'}</span></div>`
  }
}

$('#refreshExports')?.addEventListener('click',loadAll)
$('#exportList')?.addEventListener('click',event=>{const button=event.target.closest('[data-manifest]');if(button)showManifest(button.dataset.manifest,button)})
loadAll()
