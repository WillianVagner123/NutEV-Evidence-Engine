const $=selector=>document.querySelector(selector)
const esc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')
const state={context:null,application:null,overview:null,currentReview:null}

const APPLICATION_LABELS={
  GENERIC_EVIDENCE_PROJECT:'Projeto de evidências',
  SCOPING_REVIEW:'Revisão de escopo',
  INTEGRATIVE_REVIEW:'Revisão integrativa'
}
const STATUS_LABELS={assessment:'Em avaliação',ready_for_adjudication:'Pronto para adjudicação',adjudicating:'Em adjudicação',complete:'Concluído'}

async function jsonFetch(url,options={}){
  const response=await fetch(url,{cache:'no-store',credentials:'same-origin',...options})
  let payload={}
  try{payload=await response.json()}catch{}
  if(!response.ok){const error=new Error(payload?.message||payload?.error||`http_${response.status}`);error.status=response.status;error.payload=payload;throw error}
  return payload
}

function nameFor(items,id){return(items||[]).find(item=>item.id===id)?.name||''}
function appLabel(value){return APPLICATION_LABELS[String(value||'')]||String(value||'Aplicação personalizada').replaceAll('_',' ').toLocaleLowerCase('pt-BR')}
function fmtDate(value){if(!value)return'—';const date=new Date(value);return Number.isNaN(date.getTime())?'—':new Intl.DateTimeFormat('pt-BR',{dateStyle:'medium',timeStyle:'short'}).format(date)}
function textValue(value){if(value===null||value===undefined||value==='')return'—';if(typeof value==='object')return JSON.stringify(value,null,2);return String(value)}

function setHealth(label,ok=false){const node=$('#reviewHealth');node.textContent=label;node.className=`status-pill${ok?' ok':''}`}
function showError(message){$('#reviewState').className='workbench-state error';$('#reviewState').innerHTML=`<strong>Review indisponível.</strong><span>${esc(message)}</span>`;$('#reviewContent').classList.add('hidden');setHealth('indisponível')}

function renderContext(){
  const context=state.context||{}
  const current=context.current||{}
  const workspace=nameFor(context.workspaces,current.workspace_id)||'Workspace'
  const project=nameFor(context.projects,current.project_id)||'Projeto'
  const application=state.application
  $('#reviewContextTitle').textContent=application?`${project} · ${appLabel(application.application_type)}`:project
  $('#reviewContext').textContent=application?`${workspace} · aplicação ${application.id} · decisões privadas neste contexto`:`${workspace} · configure uma ResearchApplication antes de abrir Review.`
}

function renderKpis(rounds){
  const total=rounds.length
  const assigned=rounds.filter(item=>item.assigned_to_current_user).length
  const complete=rounds.filter(item=>item.status==='complete').length
  const active=rounds.filter(item=>item.status!=='complete').length
  const values=[['Rounds',total],['Em andamento',active],['Atribuídos a mim',assigned],['Concluídos',complete]]
  $('#reviewKpis').innerHTML=values.map(([label,value])=>`<article class="card metric-card"><span class="metric-label">${esc(label)}</span><strong class="metric-value">${value}</strong></article>`).join('')
}

function renderRounds(){
  const rounds=Array.isArray(state.overview?.rounds)?state.overview.rounds:[]
  renderKpis(rounds)
  const root=$('#reviewRounds')
  if(!rounds.length){
    root.innerHTML='<div class="empty-state"><strong>Nenhum round desta aplicação</strong><span>O Review genérico não importa rounds antigos por inferência. Um gestor pode criar um novo round explícito para a aplicação atual.</span></div>'
    return
  }
  root.innerHTML=rounds.map(item=>{
    const reviewers=Array.isArray(item.reviewers)?item.reviewers:[]
    const submitted=reviewers.filter(row=>row.submitted).length
    const assigned=item.assigned_to_current_user
    return `<article class="review-round-card"><div class="review-round-head"><div><span class="mini-pill">${esc(STATUS_LABELS[item.status]||item.status||'status')}</span>${assigned?'<span class="mini-pill assigned">atribuído a mim</span>':''}<h3>${esc(item.name||'Round sem nome')}</h3></div><strong>${submitted}/${reviewers.length} enviados</strong></div><div class="review-round-meta"><span>Criado ${esc(fmtDate(item.created_at))}</span><span>${reviewers.length} revisor(es)</span><span>App ${esc(item.application_id||'—')}</span></div><div class="review-round-actions">${assigned?`<button class="primary open-review" type="button" data-round-id="${esc(item.id)}">Abrir minhas atribuições</button>`:''}<button class="ghost round-details" type="button" data-round-id="${esc(item.id)}">Atualizar estado</button></div></article>`
  }).join('')
  root.querySelectorAll('.open-review').forEach(button=>button.addEventListener('click',()=>openAssignments(button.dataset.roundId)))
  root.querySelectorAll('.round-details').forEach(button=>button.addEventListener('click',()=>refreshRound(button.dataset.roundId)))
}

function renderOverview(payload){
  state.overview=payload
  state.application=payload.application||state.application
  renderContext()
  renderRounds()
  $('#createRoundPanel').classList.toggle('hidden',!payload.can_manage)
  $('#reviewState').className='hidden'
  $('#reviewContent').classList.remove('hidden')
  setHealth('contexto isolado',true)
}

async function loadOverview(){
  try{
    const payload=await jsonFetch('/api/review')
    renderOverview(payload)
  }catch(error){
    if(error.status===409&&String(error.message).includes('review_application_required')){
      $('#reviewState').className='workbench-state'
      $('#reviewState').innerHTML='<strong>Configure a aplicação de pesquisa</strong><span>Review só é habilitado depois que o projeto possui uma ResearchApplication explícita. <a href="/project.html">Abrir projeto →</a></span>'
      $('#reviewContent').classList.add('hidden')
      setHealth('aplicação necessária')
      return
    }
    if(error.status===401)return
    showError(error.status===403?'Seu papel não possui acesso à revisão deste projeto.':'Não foi possível carregar os rounds da aplicação atual.')
  }
}

async function refreshRound(roundId){
  try{
    await jsonFetch(`/api/review/rounds/${encodeURIComponent(roundId)}`)
    await loadOverview()
  }catch(error){showError(error.status===404?'O round não pertence mais à aplicação atual.':'Não foi possível atualizar o round.')}
}

async function createRound(){
  const button=$('#createReviewRound')
  const status=$('#createReviewStatus')
  const name=$('#reviewRoundName').value.trim()
  const options=$('#reviewDecisionOptions').value.split(',').map(item=>item.trim()).filter(Boolean)
  const minimum=Number.parseInt($('#reviewMinimumReviewers').value,10)
  if(!name){status.textContent='Informe o nome do round.';return}
  if(!options.length){status.textContent='Informe pelo menos uma opção de decisão.';return}
  button.disabled=true;status.textContent='Criando round…'
  try{
    await jsonFetch('/api/review/rounds',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,decision_options:options,minimum_reviewers_per_item:Number.isFinite(minimum)?minimum:2,reason_required:$('#reviewReasonRequired').checked})})
    $('#reviewRoundName').value=''
    status.textContent='Round criado e vinculado à aplicação atual.'
    await loadOverview()
  }catch(error){status.textContent=error.status===403?'Seu papel não permite criar rounds.':error.message||'Não foi possível criar o round.'}
  finally{button.disabled=false}
}

function renderPayload(payload){
  const entries=Object.entries(payload||{})
  if(!entries.length)return'<div class="small-state">Nenhum campo foi liberado para este item.</div>'
  return `<dl class="review-payload">${entries.map(([key,value])=>`<div><dt>${esc(key.replaceAll('_',' '))}</dt><dd><pre>${esc(textValue(value))}</pre></dd></div>`).join('')}</dl>`
}

function assignmentCard(item,review){
  const decision=item.decision||{}
  const locked=Boolean(review.locked)
  const options=Array.isArray(review.policy?.decision_options)?review.policy.decision_options:[]
  return `<article class="review-assignment-card" data-assignment-id="${esc(item.assignment_id)}"><div class="review-assignment-head"><strong>${esc(item.item_key||item.assignment_id)}</strong><span class="card-status${item.decision?' saved':''}">${item.decision?'Salvo':'Pendente'}</span></div>${renderPayload(item.payload)}<div class="review-decision-grid"><label>Decisão<select class="assignment-decision" ${locked?'disabled':''}><option value="">Selecione</option>${options.map(option=>`<option value="${esc(option)}" ${String(decision.decision_value||'')===String(option)?'selected':''}>${esc(option)}</option>`).join('')}</select></label><label>Justificativa<textarea class="assignment-reason" rows="3" ${locked?'disabled':''} placeholder="${review.policy?.reason_required?'Obrigatória':'Opcional'}">${esc(decision.reason||'')}</textarea></label><label>Observação<textarea class="assignment-notes" rows="2" ${locked?'disabled':''}>${esc(decision.notes||'')}</textarea></label></div><div class="review-round-actions"><button class="primary save-assignment" type="button" ${locked?'disabled':''}>${locked?'Avaliação travada':'Salvar decisão'}</button></div></article>`
}

function renderAssignments(review){
  state.currentReview=review
  const assignments=Array.isArray(review.assignments)?review.assignments:[]
  $('#assignmentPanel').classList.remove('hidden')
  $('#assignmentRoundTitle').textContent=review.round_name||'Round de revisão'
  $('#assignmentRoundMeta').textContent=`${review.completed_items||0}/${review.total_items||0} concluídos · ${review.locked?'avaliação enviada e travada':'avaliação em andamento'}`
  $('#assignmentState').className='hidden'
  $('#assignmentList').innerHTML=assignments.length?assignments.map(item=>assignmentCard(item,review)).join(''):'<div class="empty-state"><strong>Nenhum item atribuído</strong><span>O round existe, mas esta identidade ainda não recebeu itens de revisão.</span></div>'
  $('#assignmentList').querySelectorAll('.save-assignment').forEach(button=>button.addEventListener('click',()=>saveAssignment(button.closest('.review-assignment-card'))))
  const submit=$('#submitReview')
  submit.disabled=Boolean(review.locked)||!review.total_items||review.completed_items!==review.total_items
  submit.textContent=review.locked?'Avaliação enviada':'Enviar e travar avaliação'
  $('#reviewSubmitHint').textContent=review.locked?'As decisões deste revisor estão imutáveis.':`Complete todos os itens antes do envio final (${review.completed_items||0}/${review.total_items||0}).`
  $('#assignmentPanel').scrollIntoView({behavior:'smooth',block:'start'})
}

async function openAssignments(roundId){
  $('#assignmentPanel').classList.remove('hidden')
  $('#assignmentState').className='workbench-state'
  $('#assignmentState').textContent='Carregando atribuições…'
  $('#assignmentList').innerHTML=''
  try{renderAssignments(await jsonFetch(`/api/review/rounds/${encodeURIComponent(roundId)}/assignments`))}
  catch(error){
    $('#assignmentState').className='workbench-state error'
    $('#assignmentState').textContent=error.status===404?'Você não possui uma atribuição neste round.':'Não foi possível carregar suas atribuições.'
  }
}

async function saveAssignment(card){
  if(!card||!state.currentReview)return
  const button=card.querySelector('.save-assignment')
  const status=card.querySelector('.card-status')
  const decision=card.querySelector('.assignment-decision').value
  const reason=card.querySelector('.assignment-reason').value.trim()
  const notes=card.querySelector('.assignment-notes').value.trim()
  if(!decision){status.className='card-status error';status.textContent='Escolha uma decisão.';return}
  if(state.currentReview.policy?.reason_required&&!reason){status.className='card-status error';status.textContent='Informe a justificativa.';return}
  button.disabled=true;status.className='card-status';status.textContent='Salvando…'
  try{
    const payload=await jsonFetch('/api/review/decision',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({round_id:state.currentReview.round_id,assignment_id:card.dataset.assignmentId,decision_value:decision,reason,notes})})
    renderAssignments(payload)
    await loadOverview()
  }catch(error){status.className='card-status error';status.textContent=error.message||'Falha ao salvar';button.disabled=false}
}

async function submitReview(){
  if(!state.currentReview)return
  const button=$('#submitReview')
  button.disabled=true
  $('#reviewSubmitHint').textContent='Enviando e travando avaliação…'
  try{
    const payload=await jsonFetch('/api/review/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({round_id:state.currentReview.round_id})})
    renderAssignments(payload)
    await loadOverview()
  }catch(error){$('#reviewSubmitHint').textContent=error.message||'Não foi possível enviar a avaliação.';button.disabled=false}
}

async function init(){
  try{
    const auth=await jsonFetch('/api/auth/status')
    if(auth.mode!=='pilot'){showError('Review genérico requer o runtime autenticado multi-tenant.');return}
    state.context=await jsonFetch('/api/context')
    if(!state.context.current?.project_id){showError('Selecione um projeto antes de abrir Review.');return}
    const applicationPayload=await jsonFetch('/api/application')
    state.application=applicationPayload.application||null
    renderContext()
    await loadOverview()
  }catch(error){if(error.status!==401)showError('Não foi possível resolver o contexto autenticado de Review.')}
}

$('#createReviewRound')?.addEventListener('click',createRound)
$('#refreshReview')?.addEventListener('click',loadOverview)
$('#closeAssignments')?.addEventListener('click',()=>{$('#assignmentPanel').classList.add('hidden');state.currentReview=null})
$('#submitReview')?.addEventListener('click',submitReview)
init()
