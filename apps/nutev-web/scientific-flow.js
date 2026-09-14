const FLOW_STAGES=[
  {id:'map',label:'Evidence Map',note:'Estrutura do corpus',href:'/evidence-map.html'},
  {id:'intelligence',label:'Scientific Intelligence',note:'Inspeção de sinais',href:'/intelligence.html'},
  {id:'review',label:'Human Review',note:'Decisão explícita',href:'/review.html'}
]

const FLOW_PAGE={
  '/evidence-map.html':'map',
  '/intelligence.html':'intelligence',
  '/review.html':'review'
}

const flowStage=FLOW_PAGE[location.pathname]
const $flow=selector=>document.querySelector(selector)
const flowEsc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')
const flowNumber=value=>Number(String(value??'').replace(/\D/g,''))||0

function flowHref(stage){
  if(stage.id==='intelligence'&&flowStage==='map'){
    const domain=$flow('#mapDomainFilter')?.value||''
    return domain?`${stage.href}?domain=${encodeURIComponent(domain)}`:stage.href
  }
  if(stage.id==='map'&&flowStage==='intelligence'){
    const domain=$flow('#findingDomainSelect')?.value||new URLSearchParams(location.search).get('domain')||''
    return domain?`${stage.href}?domain=${encodeURIComponent(domain)}`:stage.href
  }
  return stage.href
}

function installFlowRail(){
  if(!flowStage||$flow('#scientificFlowRail'))return
  const header=document.querySelector('main > header, .main > header')
  if(!header)return
  const section=document.createElement('section')
  section.id='scientificFlowRail'
  section.className='card scientific-flow-rail'
  section.innerHTML=`
    <div class="scientific-flow-head">
      <div><span class="scientific-flow-eyebrow">SCIENTIFIC WORKFLOW</span><strong>Do mapa à decisão humana, sem atalhos científicos</strong></div>
      <span class="scientific-flow-badge">navigation only</span>
    </div>
    <div class="scientific-flow-stages" role="navigation" aria-label="Fluxo científico visual">
      ${FLOW_STAGES.map((stage,index)=>{
        const inner=`<span class="scientific-flow-index">${index+1}</span><span><strong>${flowEsc(stage.label)}</strong><small>${flowEsc(stage.note)}</small></span>`
        return stage.id===flowStage
          ?`<span class="scientific-flow-stage active" aria-current="step">${inner}</span>`
          :`<a class="scientific-flow-stage" data-flow-stage="${stage.id}" href="${flowHref(stage)}">${inner}</a>`
      }).join('')}
    </div>
    <div class="scientific-flow-context" id="scientificFlowContext"></div>
    <div class="scientific-flow-guardrail">Mapa e Intelligence organizam navegação e inspeção. Nenhum filtro, volume, recorrência ou clique cria elegibilidade, inclusão, certeza, EvidenceClaim, decisão de Review ou PRISMA.</div>`
  header.insertAdjacentElement('afterend',section)
}

function refreshFlowLinks(){
  document.querySelectorAll('a[data-flow-stage]').forEach(link=>{
    const stage=FLOW_STAGES.find(item=>item.id===link.dataset.flowStage)
    if(stage)link.href=flowHref(stage)
  })
}

function updateMapContext(){
  if(flowStage!=='map')return
  const summary=$flow('#mapFilterSummary')?.textContent?.replace(/\s+/g,' ').trim()||'Tier A estrutural'
  const domain=$flow('#mapDomainFilter')?.value||''
  const context=$flow('#scientificFlowContext')
  if(context){
    context.innerHTML=`<div><strong>Recorte atual</strong><span>${flowEsc(summary)}</span></div><a class="scientific-flow-action" href="${domain?`/intelligence.html?domain=${encodeURIComponent(domain)}`:'/intelligence.html'}">Levar domínio para Intelligence →</a>`
  }
  refreshFlowLinks()
}

function installMapBridge(){
  if(flowStage!=='map')return
  const controls=['#mapDomainFilter','#mapClassFilter','#mapRouteFilter']
  controls.forEach(selector=>$flow(selector)?.addEventListener('change',()=>queueMicrotask(updateMapContext)))
  $flow('#clearMapFilters')?.addEventListener('click',()=>queueMicrotask(updateMapContext))
  $flow('#mapViewTabs')?.addEventListener('click',()=>queueMicrotask(updateMapContext))
  const summary=$flow('#mapFilterSummary')
  if(summary)new MutationObserver(updateMapContext).observe(summary,{childList:true,subtree:true,characterData:true})
  updateMapContext()
}

function domainCards(){
  return [...document.querySelectorAll('#domainSynthesis [data-domain-card]')].map(card=>{
    const domain=card.dataset.domainCard||''
    const label=card.querySelector('h3')?.textContent?.trim()||domain
    const documents=flowNumber(card.querySelector('.domain-count')?.textContent)
    const ready=flowNumber(card.querySelector('.domain-metric strong')?.textContent)
    return {domain,label,documents,ready,active:card.classList.contains('active')}
  }).filter(item=>item.domain)
}

function renderIntelligenceOverview(){
  if(flowStage!=='intelligence')return
  const synthesis=$flow('#domainSynthesis')
  if(!synthesis)return
  let overview=$flow('#scientificDomainOverview')
  if(!overview){
    overview=document.createElement('div')
    overview.id='scientificDomainOverview'
    overview.className='scientific-domain-overview'
    synthesis.insertAdjacentElement('beforebegin',overview)
  }
  const rows=domainCards()
  if(!rows.length){overview.innerHTML='';return}
  const max=Math.max(1,...rows.map(item=>item.documents))
  overview.innerHTML=`<div class="scientific-domain-overview-head"><div><strong>Landscape do domínio</strong><span>Volume estrutural + cobertura de result bundles; não é força da evidência.</span></div><span>${rows.length} domínios</span></div><div class="scientific-domain-bars">${rows.map(item=>{
    const volume=Math.max(3,100*item.documents/max)
    const ready=item.documents?100*item.ready/item.documents:0
    return `<button type="button" class="scientific-domain-bar${item.active?' active':''}" data-flow-domain="${flowEsc(item.domain)}" title="${flowEsc(item.label)}: ${item.documents} documentos; ${item.ready} finding-ready"><span class="scientific-domain-label">${flowEsc(item.label)}</span><span class="scientific-domain-track"><i style="--flow-volume:${volume}%"><b style="--flow-ready:${ready}%"></b></i></span><span class="scientific-domain-value">${item.documents}</span></button>`
  }).join('')}</div><div class="scientific-domain-legend"><span><i class="volume"></i> documentos mapeados</span><span><i class="ready"></i> result bundle materializado</span></div>`
  overview.querySelectorAll('[data-flow-domain]').forEach(button=>button.addEventListener('click',()=>{
    const target=synthesis.querySelector(`[data-select-domain="${CSS.escape(button.dataset.flowDomain)}"]`)
    target?.click()
  }))
  updateIntelligenceContext()
}

function updateIntelligenceContext(){
  if(flowStage!=='intelligence')return
  const select=$flow('#findingDomainSelect')
  const domain=select?.value||''
  const label=select?.selectedOptions?.[0]?.textContent?.trim()||'Nenhum domínio selecionado'
  const context=$flow('#scientificFlowContext')
  if(context){
    context.innerHTML=`<div><strong>Domínio em inspeção</strong><span>${flowEsc(label)}</span></div><div class="scientific-flow-actions"><a class="scientific-flow-action secondary" href="${domain?`/evidence-map.html?domain=${encodeURIComponent(domain)}`:'/evidence-map.html'}">Ver no mapa</a><a class="scientific-flow-action" href="/review.html">Abrir Human Review →</a></div>`
  }
  refreshFlowLinks()
}

function hydrateIntelligenceDomain(){
  if(flowStage!=='intelligence')return
  const requested=new URLSearchParams(location.search).get('domain')||''
  if(!requested)return
  const wrap=$flow('#findingDomainSelectWrap')
  if(!wrap)return
  const apply=()=>{
    const select=$flow('#findingDomainSelect')
    if(!select||select.dataset.flowHydrated==='1')return
    const option=[...select.options].find(item=>item.value===requested)
    if(!option)return
    select.dataset.flowHydrated='1'
    select.value=requested
    select.dispatchEvent(new Event('change',{bubbles:true}))
  }
  new MutationObserver(apply).observe(wrap,{childList:true,subtree:true})
  apply()
}

function installIntelligenceBridge(){
  if(flowStage!=='intelligence')return
  const synthesis=$flow('#domainSynthesis')
  if(synthesis)new MutationObserver(renderIntelligenceOverview).observe(synthesis,{childList:true,subtree:true,attributes:true,attributeFilter:['class']})
  const wrap=$flow('#findingDomainSelectWrap')
  if(wrap)new MutationObserver(()=>{
    const select=$flow('#findingDomainSelect')
    if(select&&!select.dataset.flowBound){
      select.dataset.flowBound='1'
      select.addEventListener('change',()=>queueMicrotask(()=>{renderIntelligenceOverview();updateIntelligenceContext()}))
    }
    updateIntelligenceContext()
  }).observe(wrap,{childList:true,subtree:true})
  hydrateIntelligenceDomain()
  renderIntelligenceOverview()
  updateIntelligenceContext()
}

function reviewProgressValues(){
  const meta=$flow('#assignmentRoundMeta')?.textContent||''
  const match=meta.match(/(\d+)\s*\/\s*(\d+)\s*concluídos/i)
  if(match)return {completed:Number(match[1]),total:Number(match[2]),locked:/travada|enviada/i.test(meta)}
  const cards=[...document.querySelectorAll('#assignmentList .review-assignment-card')]
  const completed=cards.filter(card=>card.querySelector('.card-status.saved')).length
  return {completed,total:cards.length,locked:/travada|enviada/i.test(meta)}
}

function renderReviewProgress(){
  if(flowStage!=='review')return
  const panel=$flow('#assignmentPanel')
  if(!panel)return
  let node=$flow('#reviewVisualProgress')
  if(!node){
    node=document.createElement('div')
    node.id='reviewVisualProgress'
    node.className='review-visual-progress'
    const head=panel.querySelector('.product-panel-head')
    head?.insertAdjacentElement('afterend',node)
  }
  const {completed,total,locked}=reviewProgressValues()
  const percent=total?Math.round(100*completed/total):0
  node.innerHTML=`<div class="review-progress-copy"><span>${locked?'Avaliação travada':'Progresso desta avaliação'}</span><strong>${completed}/${total||0} itens${total?` · ${percent}%`:''}</strong><small>${locked?'Decisões enviadas e imutáveis para este revisor.':'Progresso operacional da atribuição; não é taxa de inclusão nem resultado científico.'}</small></div><div class="review-progress-track" role="progressbar" aria-label="Itens de revisão concluídos" aria-valuemin="0" aria-valuemax="${total||0}" aria-valuenow="${completed}"><i style="--review-progress:${percent}%"></i></div>`
}

function updateReviewContext(){
  if(flowStage!=='review')return
  const context=$flow('#scientificFlowContext')
  if(context)context.innerHTML='<div><strong>Etapa humana isolada</strong><span>Workspace, projeto e ResearchApplication governam esta página. O recorte visual anterior não é importado como decisão.</span></div><a class="scientific-flow-action secondary" href="/intelligence.html">Voltar à Intelligence</a>'
}

function installReviewBridge(){
  if(flowStage!=='review')return
  const list=$flow('#assignmentList')
  const meta=$flow('#assignmentRoundMeta')
  if(list)new MutationObserver(renderReviewProgress).observe(list,{childList:true,subtree:true,attributes:true,attributeFilter:['class']})
  if(meta)new MutationObserver(renderReviewProgress).observe(meta,{childList:true,subtree:true,characterData:true})
  renderReviewProgress()
  updateReviewContext()
}

function initScientificFlow(){
  installFlowRail()
  installMapBridge()
  installIntelligenceBridge()
  installReviewBridge()
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initScientificFlow,{once:true})
else initScientificFlow()
