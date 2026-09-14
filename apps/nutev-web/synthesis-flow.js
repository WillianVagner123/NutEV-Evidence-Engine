import {t} from './i18n.js'

const FLOW_STAGES=[
  {id:'review',label:()=>t('Revisão de Síntese','Synthesis Review'),note:()=>t('Julgamento humano explícito','Explicit human judgment'),path:'/synthesis-review.html'},
  {id:'brief',label:()=>t('Resumo de Síntese Verificado','Verified Synthesis Summary'),note:()=>t('Integridade + contexto','Integrity + context'),path:'/synthesis-brief.html'},
  {id:'ask',label:()=>t('Consulta de Evidências','Evidence Query'),note:()=>t('Consulta vinculada às fontes','Source-linked evidence query'),path:'/ask.html'}
]

const FLOW_PAGE={
  '/synthesis-review.html':'review',
  '/synthesis-brief.html':'brief',
  '/ask.html':'ask'
}

const flowStage=FLOW_PAGE[location.pathname]
const $flow=selector=>document.querySelector(selector)
const flowEsc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')

function installFlowCss(){
  if(document.querySelector('link[data-synthesis-flow-css]'))return
  const link=document.createElement('link')
  link.rel='stylesheet'
  link.href='./synthesis-flow.css'
  link.dataset.synthesisFlowCss='1'
  document.head.appendChild(link)
}

function flowMetric(label,value,note=''){
  return `<div class="synthesis-flow-metric"><span>${flowEsc(label)}</span><strong>${flowEsc(value)}</strong>${note?`<small>${flowEsc(note)}</small>`:''}</div>`
}

function flowButton(label,target,kind=''){
  return `<button type="button" class="synthesis-flow-action${kind?` ${kind}`:''}" data-synthesis-flow-target="${flowEsc(target)}">${flowEsc(label)}</button>`
}

function localButton(label,action,kind=''){
  return `<button type="button" class="synthesis-flow-action${kind?` ${kind}`:''}" data-synthesis-flow-action="${flowEsc(action)}">${flowEsc(label)}</button>`
}

function installRail(){
  if(!flowStage)return
  document.querySelector('#synthesisResearchFlow')?.remove()
  const header=document.querySelector('main > header, .main > header')
  if(!header)return
  const section=document.createElement('section')
  section.id='synthesisResearchFlow'
  section.className='card synthesis-flow-rail'
  section.innerHTML=`
    <div class="synthesis-flow-head">
      <div><span class="synthesis-flow-eyebrow">${t('ESPAÇO DE SÍNTESE DE PESQUISA','RESEARCH SYNTHESIS AREA')}</span><strong>${t('Da revisão humana à consulta vinculada às fontes — sem promoção automática','From human review to source-linked evidence query — without automatic promotion')}</strong></div>
      <span class="synthesis-flow-badge">${t('somente navegação','navigation only')}</span>
    </div>
    <div class="synthesis-flow-stages" role="navigation" aria-label="${t('Fluxo de síntese e consulta','Synthesis and query flow')}">
      ${FLOW_STAGES.map((stage,index)=>stage.id===flowStage
        ? `<div class="synthesis-flow-stage active" aria-current="step"><span class="synthesis-flow-index">${index+1}</span><span><strong>${flowEsc(stage.label())}</strong><small>${flowEsc(stage.note())}</small></span></div>`
        : `<button type="button" class="synthesis-flow-stage" data-synthesis-flow-target="${flowEsc(stage.path)}"><span class="synthesis-flow-index">${index+1}</span><span><strong>${flowEsc(stage.label())}</strong><small>${flowEsc(stage.note())}</small></span></button>`
      ).join('')}
    </div>
    <div class="synthesis-flow-context" id="synthesisFlowContext"></div>
    <div class="synthesis-flow-guardrail">${t('Revisão, Resumo e Consulta são superfícies distintas. Navegar entre elas não cria síntese canônica, EvidenceClaim, elegibilidade, risco de viés, certeza, recomendação, PRESS, GF-10 ou PRISMA. A Consulta de Evidências não importa automaticamente decisões da Revisão nem do Resumo.','Review, Summary, and Query are distinct surfaces. Navigating between them does not create canonical synthesis, an EvidenceClaim, eligibility, risk of bias, certainty, recommendation, PRESS, GF-10, or PRISMA. Evidence Query does not automatically import decisions from Review or Summary.')}</div>`
  header.insertAdjacentElement('afterend',section)
  section.addEventListener('click',handleFlowClick)
}

function handleFlowClick(event){
  const nav=event.target.closest('[data-synthesis-flow-target]')
  if(nav){location.assign(nav.dataset.synthesisFlowTarget);return}
  const action=event.target.closest('[data-synthesis-flow-action]')?.dataset.synthesisFlowAction
  if(action==='export-review')$flow('#exportReview')?.click()
  if(action==='build-packet')$flow('#buildPacket')?.click()
}

function progressValues(){
  const text=$flow('#reviewProgress')?.textContent||''
  const match=text.match(/(\d+)\s*\/\s*(\d+)/)
  return match?{done:Number(match[1]),total:Number(match[2])}:{done:0,total:0}
}

function updateReviewContext(){
  if(flowStage!=='review')return
  const context=$flow('#synthesisFlowContext')
  if(!context)return
  const reviewer=$flow('#reviewerName')?.value?.trim()||t('não identificado','not identified')
  const {done,total}=progressValues()
  const recordCount=document.querySelectorAll('#reviewLedger .ledger-row').length
  const health=$flow('#reviewHealth')?.textContent?.trim()||t('rascunho local','local draft')
  context.innerHTML=`
    <div class="synthesis-flow-context-head"><div><strong>${t('Estado operacional da Revisão','Review operational state')}</strong><span>${t('Rascunho local · canonical:false · nenhuma decisão é promovida automaticamente.','Local draft · canonical:false · no decision is promoted automatically.')}</span></div><span class="synthesis-flow-status">${flowEsc(health)}</span></div>
    <div class="synthesis-flow-metrics">
      ${flowMetric(t('Revisor','Reviewer'),reviewer,reviewer===t('não identificado','not identified')?t('obrigatório antes da exportação','required before export'):t('identidade declarada; não autenticada','declared identity; not authenticated'))}
      ${flowMetric(t('Comparações da âncora','Anchor comparisons'),`${done}/${total}`,total?t('julgamentos salvos no recorte atual','judgments saved in the current slice'):t('aguardando achados','waiting for findings'))}
      ${flowMetric(t('Registro local','Local record'),String(recordCount),t('decisões humanas neste navegador','human decisions in this browser'))}
    </div>
    <div class="synthesis-flow-actions">
      ${localButton(t('Exportar revisão','Export review'),'export-review')}
      ${flowButton(t('Abrir Resumo →','Open Summary →'),'/synthesis-brief.html','primary')}
    </div>
    <p class="synthesis-flow-note">${t('O Resumo não recebe o rascunho por memória ou URL. Para circular o julgamento, exporte o artefato e importe-o no Resumo, onde SHA-256 e a impressão digital do contexto serão verificados novamente.','The Summary does not receive the draft through memory or URL. To transfer the judgment, export the artifact and import it into the Summary, where SHA-256 and the context fingerprint are verified again.')}</p>`
}

function installReviewState(){
  if(flowStage!=='review')return
  for(const selector of ['#reviewProgress','#reviewLedger','#reviewHealth']){
    const node=$flow(selector)
    if(node)new MutationObserver(updateReviewContext).observe(node,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['class']})
  }
  $flow('#reviewerName')?.addEventListener('input',updateReviewContext)
  $flow('#reviewDomain')?.addEventListener('change',()=>queueMicrotask(updateReviewContext))
  $flow('#anchorFinding')?.addEventListener('change',()=>queueMicrotask(updateReviewContext))
  updateReviewContext()
}

function briefVerificationValues(){
  const pass=document.querySelectorAll('#verificationGrid .verify-item.pass').length
  const fail=document.querySelectorAll('#verificationGrid .verify-item.fail').length
  return {pass,fail}
}

function updateBriefContext(){
  if(flowStage!=='brief')return
  const context=$flow('#synthesisFlowContext')
  if(!context)return
  const healthNode=$flow('#briefHealth')
  const verified=Boolean(healthNode?.classList.contains('ok'))&&!$flow('#exportBrief')?.disabled
  const {pass,fail}=briefVerificationValues()
  const decisions=[...document.querySelectorAll('#briefKpis .kpi-card')].find(card=>['decisões humanas','human decisions'].includes(card.querySelector('span')?.textContent?.trim()?.toLocaleLowerCase()))?.querySelector('strong')?.textContent?.trim()||'—'
  context.innerHTML=`
    <div class="synthesis-flow-context-head"><div><strong>${t('Estado operacional do Resumo','Summary operational state')}</strong><span>${verified?t('Artefato humano compatível com o contexto atual.','Human artifact compatible with the current context.'):t('Importe uma Revisão exportada para executar a verificação com bloqueio por segurança.','Import an exported Review to run fail-closed verification.')}</span></div><span class="synthesis-flow-status${verified?' ok':''}">${flowEsc(healthNode?.textContent?.trim()||t('aguardando revisão','waiting for review'))}</span></div>
    <div class="synthesis-flow-metrics">
      ${flowMetric(t('Verificações','Checks'),`${pass} ${t('aprovadas','pass')}${fail?` · ${fail} ${t('falharam','fail')}`:''}`,verified?t('integridade e contexto satisfeitos','integrity and context satisfied'):t('o Resumo permanece bloqueado até todas as verificações passarem','Summary remains locked until all checks pass'))}
      ${flowMetric(t('Decisões humanas','Human decisions'),decisions,t('descrição do artefato; não é força da evidência','artifact description; not evidence strength'))}
      ${flowMetric(t('Semântica','Semantics'),verified?t('verificado + não canônico','verified + noncanonical'):t('não canônico','noncanonical'),t('integridade verificada ≠ validado cientificamente','integrity verified ≠ scientifically validated'))}
    </div>
    <div class="synthesis-flow-actions">
      ${flowButton(t('← Voltar à Revisão','← Back to Review'),'/synthesis-review.html','secondary')}
      ${flowButton(t('Abrir Consulta de Evidências →','Open Evidence Query →'),'/ask.html','primary')}
    </div>
    <p class="synthesis-flow-note">${t('Abrir a Consulta de Evidências inicia uma superfície separada. Nenhum rótulo de relação, justificativa, SHA do Resumo ou decisão humana é enviado à Consulta como evidência ou filtro científico.','Opening Evidence Query starts a separate surface. No relation label, rationale, Summary SHA or human decision is sent to the Query as evidence or a scientific filter.')}</p>`
}

function installBriefState(){
  if(flowStage!=='brief')return
  for(const selector of ['#briefHealth','#verificationGrid','#briefKpis','#briefContent']){
    const node=$flow(selector)
    if(node)new MutationObserver(updateBriefContext).observe(node,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['class','disabled']})
  }
  $flow('#reviewFile')?.addEventListener('change',()=>queueMicrotask(updateBriefContext))
  updateBriefContext()
}

function askPacketReady(){return Boolean($flow('#contextPacket')?.value?.trim())}

function updateAskContext(){
  if(flowStage!=='ask')return
  const context=$flow('#synthesisFlowContext')
  if(!context)return
  const healthNode=$flow('#askHealth')
  const ready=Boolean(healthNode?.classList.contains('ok'))
  const resultMeta=$flow('#askResultMeta')?.textContent?.trim()||t('nenhuma consulta executada','no query executed')
  const selected=$flow('#selectedCount')?.textContent?.trim()||t('0 selecionados','0 selected')
  const packet=askPacketReady()
  context.innerHTML=`
    <div class="synthesis-flow-context-head"><div><strong>${t('Estado operacional da Consulta','Query operational state')}</strong><span>${t('Consulta determinística sobre o contexto verificado do Artigo 1; não toma decisões científicas.','Deterministic query over the verified Article 1 context; it does not make scientific decisions.')}</span></div><span class="synthesis-flow-status${ready?' ok':''}">${flowEsc(healthNode?.textContent?.trim()||t('carregando contexto','loading context'))}</span></div>
    <div class="synthesis-flow-metrics">
      ${flowMetric(t('Contexto','Context'),ready?t('disponível','available'):t('indisponível / carregando','unavailable / loading'),t('resumos estruturados sem uso de ranking científico','structured summaries without scientific ranking'))}
      ${flowMetric(t('Consulta','Query'),resultMeta,t('correspondência lexical ≠ relevância científica validada','lexical match ≠ validated scientific relevance'))}
      ${flowMetric(t('Seleção','Selection'),selected,packet?t('pacote de evidências materializado','evidence packet materialized'):t('pacote de evidências ainda não materializado','evidence packet not yet materialized'))}
    </div>
    <div class="synthesis-flow-actions">
      ${flowButton(t('← Ver Resumo','← View Summary'),'/synthesis-brief.html','secondary')}
      ${localButton(t('Gerar pacote de evidências','Build evidence packet'),'build-packet','primary')}
    </div>
    <p class="synthesis-flow-note">${t('A Consulta de Evidências não lê a Revisão nem o Resumo. O pacote usa apenas a pergunta, os filtros e os documentos selecionados na superfície verificada de consulta.','Evidence Query does not read Review or Summary. The packet uses only the question, filters and documents selected on the verified query surface.')}</p>`
}

function installAskState(){
  if(flowStage!=='ask')return
  for(const selector of ['#askHealth','#askResultMeta','#selectedCount','#askResults','#askContent']){
    const node=$flow(selector)
    if(node)new MutationObserver(updateAskContext).observe(node,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['class']})
  }
  for(const selector of ['#runAsk','#buildPacket','#clearAsk','.ask-suggestions','#askResults']){
    $flow(selector)?.addEventListener('click',()=>setTimeout(updateAskContext,0))
  }
  for(const selector of ['#askRoute','#askDomain','#askClass'])$flow(selector)?.addEventListener('change',()=>setTimeout(updateAskContext,0))
  $flow('#contextPacket')?.addEventListener('input',updateAskContext)
  updateAskContext()
}

function renderFlow(){
  installFlowCss()
  installRail()
  updateReviewContext()
  updateBriefContext()
  updateAskContext()
}

function initSynthesisFlow(){
  if(!flowStage)return
  renderFlow()
  installReviewState()
  installBriefState()
  installAskState()
  window.addEventListener('nutev:language-change',renderFlow)
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initSynthesisFlow,{once:true})
else initSynthesisFlow()