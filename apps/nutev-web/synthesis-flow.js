import './i18n.js'

const FLOW_STAGES=[
  {id:'review',label:'Human Synthesis Review',note:'Julgamento humano explícito',path:'/synthesis-review.html'},
  {id:'brief',label:'Verified Synthesis Brief',note:'Integridade + contexto',path:'/synthesis-brief.html'},
  {id:'ask',label:'Ask NutEV',note:'Grounded retrieval',path:'/ask.html'}
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
  if(!flowStage||$flow('#synthesisResearchFlow'))return
  const header=document.querySelector('main > header, .main > header')
  if(!header)return
  const section=document.createElement('section')
  section.id='synthesisResearchFlow'
  section.className='card synthesis-flow-rail'
  section.innerHTML=`
    <div class="synthesis-flow-head">
      <div><span class="synthesis-flow-eyebrow">RESEARCH SYNTHESIS WORKSPACE</span><strong>Do julgamento humano ao retrieval grounded — sem promoção automática</strong></div>
      <span class="synthesis-flow-badge">navigation only</span>
    </div>
    <div class="synthesis-flow-stages" role="navigation" aria-label="Fluxo de síntese e retrieval">
      ${FLOW_STAGES.map((stage,index)=>stage.id===flowStage
        ? `<div class="synthesis-flow-stage active" aria-current="step"><span class="synthesis-flow-index">${index+1}</span><span><strong>${flowEsc(stage.label)}</strong><small>${flowEsc(stage.note)}</small></span></div>`
        : `<button type="button" class="synthesis-flow-stage" data-synthesis-flow-target="${flowEsc(stage.path)}"><span class="synthesis-flow-index">${index+1}</span><span><strong>${flowEsc(stage.label)}</strong><small>${flowEsc(stage.note)}</small></span></button>`
      ).join('')}
    </div>
    <div class="synthesis-flow-context" id="synthesisFlowContext"></div>
    <div class="synthesis-flow-guardrail">Review, Brief e Ask são superfícies distintas. Navegar entre elas não cria canonical synthesis, EvidenceClaim, elegibilidade, RoB, certainty, recomendação, PRESS, GF-10 ou PRISMA. Ask NutEV não importa automaticamente decisões do Review nem o Brief.</div>`
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
  const reviewer=$flow('#reviewerName')?.value?.trim()||'não identificado'
  const {done,total}=progressValues()
  const ledgerCount=document.querySelectorAll('#reviewLedger .ledger-row').length
  const health=$flow('#reviewHealth')?.textContent?.trim()||'rascunho local'
  context.innerHTML=`
    <div class="synthesis-flow-context-head"><div><strong>Estado operacional do Review</strong><span>Rascunho local · <code>canonical:false</code> · nenhuma decisão é promovida automaticamente.</span></div><span class="synthesis-flow-status">${flowEsc(health)}</span></div>
    <div class="synthesis-flow-metrics">
      ${flowMetric('Revisor',reviewer,reviewer==='não identificado'?'obrigatório antes do export':'identidade declarada; não autenticada')}
      ${flowMetric('Comparações da âncora',`${done}/${total}`,total?'julgamentos salvos no recorte atual':'aguardando achados')}
      ${flowMetric('Ledger local',String(ledgerCount),'decisões humanas neste navegador')}
    </div>
    <div class="synthesis-flow-actions">
      ${localButton('Exportar revisão','export-review')}
      ${flowButton('Abrir Brief →','/synthesis-brief.html','primary')}
    </div>
    <p class="synthesis-flow-note">O Brief não recebe o rascunho por memória ou URL. Para circular o julgamento, exporte o artefato e importe-o no Brief, onde SHA-256 e context fingerprint serão verificados novamente.</p>`
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
  const decisions=[...document.querySelectorAll('#briefKpis .kpi-card')].find(card=>card.querySelector('span')?.textContent?.trim()==='Human decisions')?.querySelector('strong')?.textContent?.trim()||'—'
  context.innerHTML=`
    <div class="synthesis-flow-context-head"><div><strong>Estado operacional do Brief</strong><span>${verified?'Artefato humano compatível com o contexto atual.':'Importe um Review exportado para executar a verificação fail-closed.'}</span></div><span class="synthesis-flow-status${verified?' ok':''}">${flowEsc(healthNode?.textContent?.trim()||'aguardando revisão')}</span></div>
    <div class="synthesis-flow-metrics">
      ${flowMetric('Verificações',`${pass} pass${fail?` · ${fail} fail`:''}`,verified?'integridade/contexto satisfeitos':'Brief permanece bloqueado até todos os checks passarem')}
      ${flowMetric('Human decisions',decisions,'descrição do artefato; não é força da evidência')}
      ${flowMetric('Semântica',verified?'verified + noncanonical':'noncanonical','integrity verified ≠ scientifically validated')}
    </div>
    <div class="synthesis-flow-actions">
      ${flowButton('← Voltar ao Review','/synthesis-review.html','secondary')}
      ${flowButton('Abrir Ask NutEV →','/ask.html','primary')}
    </div>
    <p class="synthesis-flow-note">Abrir Ask NutEV inicia uma superfície de retrieval separada. Nenhum relation label, rationale, SHA do Brief ou decisão humana é enviado ao Ask como evidência ou filtro científico.</p>`
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
  const resultMeta=$flow('#askResultMeta')?.textContent?.trim()||'nenhuma consulta executada'
  const selected=$flow('#selectedCount')?.textContent?.trim()||'0 selecionados'
  const packet=askPacketReady()
  context.innerHTML=`
    <div class="synthesis-flow-context-head"><div><strong>Estado operacional do Ask</strong><span>Retrieval determinístico sobre o contexto seguro do Article 1; 0 chamadas externas de LLM.</span></div><span class="synthesis-flow-status${ready?' ok':''}">${flowEsc(healthNode?.textContent?.trim()||'carregando contexto')}</span></div>
    <div class="synthesis-flow-metrics">
      ${flowMetric('Contexto',ready?'disponível':'indisponível / carregando','ARTICLE_SUMMARIES rank-blind')}
      ${flowMetric('Retrieval',resultMeta,'correspondência lexical ≠ relevância científica validada')}
      ${flowMetric('Seleção',selected,packet?'context packet materializado':'context packet ainda não materializado')}
    </div>
    <div class="synthesis-flow-actions">
      ${flowButton('← Ver Brief','/synthesis-brief.html','secondary')}
      ${localButton('Gerar contexto grounded','build-packet','primary')}
    </div>
    <p class="synthesis-flow-note">Ask NutEV não lê o Review nem o Brief. O pacote grounded usa apenas a pergunta, filtros e documentos selecionados da superfície segura de retrieval.</p>`
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

function initSynthesisFlow(){
  if(!flowStage)return
  installFlowCss()
  installRail()
  installReviewState()
  installBriefState()
  installAskState()
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initSynthesisFlow,{once:true})
else initSynthesisFlow()
