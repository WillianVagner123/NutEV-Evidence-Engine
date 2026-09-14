import './i18n.js'

const CYCLE_STAGES=[
  {id:'radar',label:'Evidence Radar',note:'Observe coverage, gaps and change',path:'/radar.html'},
  {id:'strategy',label:'Strategy Lab',note:'Prepare pre-PRESS decisions',path:'/strategy.html'},
  {id:'quality',label:'Quality Observatory',note:'Verify operational integrity',path:'/quality.html'}
]

const CYCLE_PAGE={
  '/radar.html':'radar',
  '/strategy.html':'strategy',
  '/quality.html':'quality'
}

const cycleStage=CYCLE_PAGE[location.pathname]
const $cycle=selector=>document.querySelector(selector)
const cycleEsc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')

function installCycleCss(){
  if(document.querySelector('link[data-operational-cycle-css]'))return
  const link=document.createElement('link')
  link.rel='stylesheet'
  link.href='./operational-cycle.css'
  link.dataset.operationalCycleCss='1'
  document.head.appendChild(link)
}

function cycleMetric(label,value,note=''){
  return `<div class="operational-cycle-metric"><span>${cycleEsc(label)}</span><strong>${cycleEsc(value)}</strong>${note?`<small>${cycleEsc(note)}</small>`:''}</div>`
}

function cycleButton(label,target,kind=''){
  return `<button type="button" class="operational-cycle-action${kind?` ${kind}`:''}" data-operational-cycle-target="${cycleEsc(target)}">${cycleEsc(label)}</button>`
}

function localButton(label,action,kind=''){
  return `<button type="button" class="operational-cycle-action${kind?` ${kind}`:''}" data-operational-cycle-action="${cycleEsc(action)}">${cycleEsc(label)}</button>`
}

function cardMetric(container,label){
  const nodes=[...document.querySelectorAll(`${container} article, ${container} > div`)]
  const match=nodes.find(node=>{
    const labelNode=node.querySelector('.metric-label, span')
    return labelNode?.textContent?.trim()===label
  })
  return match?.querySelector('.metric-value, strong')?.textContent?.trim()||'—'
}

function installCycleRail(){
  if(!cycleStage||$cycle('#operationalResearchCycle'))return
  const header=document.querySelector('main > header, .main > header')
  if(!header)return
  const section=document.createElement('section')
  section.id='operationalResearchCycle'
  section.className='card operational-cycle-rail'
  section.innerHTML=`
    <div class="operational-cycle-head">
      <div><span class="operational-cycle-eyebrow">OPERATIONAL RESEARCH CYCLE</span><strong>Observe → Prepare → Verify, sem promoção científica automática</strong></div>
      <span class="operational-cycle-badge">navigation only</span>
    </div>
    <div class="operational-cycle-stages" role="navigation" aria-label="Ciclo operacional de pesquisa">
      ${CYCLE_STAGES.map((stage,index)=>stage.id===cycleStage
        ? `<div class="operational-cycle-stage active" aria-current="step"><span class="operational-cycle-index">${index+1}</span><span><strong>${cycleEsc(stage.label)}</strong><small>${cycleEsc(stage.note)}</small></span></div>`
        : `<button type="button" class="operational-cycle-stage" data-operational-cycle-target="${cycleEsc(stage.path)}"><span class="operational-cycle-index">${index+1}</span><span><strong>${cycleEsc(stage.label)}</strong><small>${cycleEsc(stage.note)}</small></span></button>`
      ).join('')}
    </div>
    <div class="operational-cycle-context" id="operationalCycleContext"></div>
    <div class="operational-cycle-guardrail">Radar, Strategy Lab e Quality Observatory são superfícies operacionais distintas. Navegar entre elas não aprova query, não autoriza PRESS/GF-10, não congela busca, não cria elegibilidade, RoB, certainty, EvidenceClaim, recomendação ou PRISMA.</div>`
  header.insertAdjacentElement('afterend',section)
  section.addEventListener('click',handleCycleClick)
}

function handleCycleClick(event){
  const nav=event.target.closest('[data-operational-cycle-target]')
  if(nav){location.assign(nav.dataset.operationalCycleTarget);return}
  const action=event.target.closest('[data-operational-cycle-action]')?.dataset.operationalCycleAction
  if(action==='refresh-radar')$cycle('#refreshRadar')?.click()
  if(action==='watch-radar')$cycle('#jumpChanges')?.click()
  if(action==='refresh-quality')$cycle('#refreshQuality')?.click()
}

function updateRadarContext(){
  if(cycleStage!=='radar')return
  const context=$cycle('#operationalCycleContext')
  if(!context)return
  const health=$cycle('#radarHealth')?.textContent?.trim()||'verificando engine'
  const ready=Boolean($cycle('#radarHealth')?.classList.contains('ok'))&&!$cycle('#radarContent')?.classList.contains('hidden')
  const gaps=cardMetric('#summaryCards','Tópicos com gaps')
  const active=cardMetric('#summaryCards','Busca ativa requerida')
  const providers=cardMetric('#summaryCards','Providers observados')
  const watch=$cycle('#watchBadge')?.textContent?.trim()||'aguardando'
  context.innerHTML=`
    <div class="operational-cycle-context-head"><div><strong>Estado operacional do Radar</strong><span>Cobertura, gaps e mudança longitudinal; prioridade operacional não é grau de evidência.</span></div><span class="operational-cycle-status${ready?' ok':''}">${cycleEsc(health)}</span></div>
    <div class="operational-cycle-metrics">
      ${cycleMetric('Gaps técnicos',gaps,'flags de cobertura/completude; não exclusão')}
      ${cycleMetric('Busca ativa',active,'fila P1–P3/gap; não recomendação de inclusão')}
      ${cycleMetric('Providers / Watch',`${providers} · ${watch}`,'disponibilidade e mudança operacional')}
    </div>
    <div class="operational-cycle-actions">
      ${localButton('Atualizar Radar','refresh-radar')}
      ${localButton('Ver Watch','watch-radar','secondary')}
      ${cycleButton('Abrir Strategy Lab →','/strategy.html','primary')}
    </div>
    <p class="operational-cycle-note">Abrir Strategy Lab não converte gaps, volume, prioridade ou eventos do Watch em termos de busca. As decisões de vocabulário continuam explícitas e pré-PRESS.</p>`
}

function installRadarState(){
  if(cycleStage!=='radar')return
  for(const selector of ['#radarHealth','#radarContent','#summaryCards','#watchBadge','#watchSummary']){
    const node=$cycle(selector)
    if(node)new MutationObserver(updateRadarContext).observe(node,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['class']})
  }
  updateRadarContext()
}

function updateStrategyContext(){
  if(cycleStage!=='strategy')return
  const context=$cycle('#operationalCycleContext')
  if(!context)return
  const health=$cycle('#strategyHealth')?.textContent?.trim()||'carregando draft'
  const loaded=Boolean($cycle('#strategyHealth')?.classList.contains('ok'))&&!$cycle('#strategyContent')?.classList.contains('hidden')
  const press=cardMetric('#strategyReadiness','PRESS')
  const gf10=cardMetric('#strategyReadiness','GF-10')
  const freeze=cardMetric('#strategyReadiness','Query freeze')
  const formal=cardMetric('#strategyReadiness','Formal search')
  const deltas=document.querySelectorAll('#deltaTests .delta-test').length
  context.innerHTML=`
    <div class="operational-cycle-context-head"><div><strong>Estado operacional da Strategy</strong><span>Draft pré-PRESS em leitura/comparação; a interface não aprova nem executa busca formal.</span></div><span class="operational-cycle-status${loaded?' ok':''}">${cycleEsc(health)}</span></div>
    <div class="operational-cycle-metrics">
      ${cycleMetric('PRESS / GF-10',`${press} · ${gf10}`,'estado canônico refletido, nunca inferido')}
      ${cycleMetric('Freeze / Formal',`${freeze} · ${formal}`,'fail-closed até os gates reais')}
      ${cycleMetric('Delta tests',String(deltas),'itens candidatos aguardando avaliação PRESS')}
    </div>
    <div class="operational-cycle-actions">
      ${cycleButton('← Evidence Radar','/radar.html','secondary')}
      ${cycleButton('Abrir QA','/review-qa.html')}
      ${cycleButton('Abrir PRESS','/press-review.html')}
      ${cycleButton('Quality Observatory →','/quality.html','primary')}
    </div>
    <p class="operational-cycle-note">Frequência, gaps e provider status não promovem termos. PASS de PRESS, autorização GF-10, query freeze e execução formal continuam dependentes dos contratos canônicos existentes.</p>`
}

function installStrategyState(){
  if(cycleStage!=='strategy')return
  for(const selector of ['#strategyHealth','#strategyContent','#strategyReadiness','#deltaTests','#draftStatus']){
    const node=$cycle(selector)
    if(node)new MutationObserver(updateStrategyContext).observe(node,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['class']})
  }
  updateStrategyContext()
}

function updateQualityContext(){
  if(cycleStage!=='quality')return
  const context=$cycle('#operationalCycleContext')
  if(!context)return
  const health=$cycle('#qualityHealth')?.textContent?.trim()||'verificando'
  const ready=!$cycle('#qualityContent')?.classList.contains('hidden')
  const fullText=cardMetric('#qualityKpis','Full-text coverage')
  const age=cardMetric('#qualityKpis','Context age')
  const unclassified=cardMetric('#qualityKpis','Unclassified')
  const errors=document.querySelectorAll('#qualityContent .quality-check.error').length
  const attention=document.querySelectorAll('#qualityContent .quality-check.attention, #qualityContent .quality-provider.attention').length
  context.innerHTML=`
    <div class="operational-cycle-context-head"><div><strong>Estado operacional do Observatory</strong><span>Saúde do sistema, integridade e completude técnica; não é avaliação metodológica da evidência.</span></div><span class="operational-cycle-status${ready&&errors===0?' ok':''}">${cycleEsc(health)}</span></div>
    <div class="operational-cycle-metrics">
      ${cycleMetric('Full-text coverage',fullText,'retrieval técnico; não screening ou certainty')}
      ${cycleMetric('Context age / Unclassified',`${age} · ${unclassified}`,'freshness e completude operacional')}
      ${cycleMetric('Checks',`${errors} erro${errors===1?'':'s'} · ${attention} atenção`,'observabilidade do sistema; sem score científico')}
    </div>
    <div class="operational-cycle-actions">
      ${cycleButton('← Strategy Lab','/strategy.html','secondary')}
      ${localButton('Atualizar Observatory','refresh-quality')}
      ${cycleButton('Voltar ao Radar ↺','/radar.html','primary')}
    </div>
    <p class="operational-cycle-note">Quality Observatory não autoriza Strategy, não valida estudos e não produz evidence-quality score. Erro de provider significa indisponibilidade operacional — nunca ausência de literatura.</p>`
}

function installQualityState(){
  if(cycleStage!=='quality')return
  for(const selector of ['#qualityHealth','#qualityContent','#qualityKpis','#serviceChecks','#guardrailChecks','#qualityProviders']){
    const node=$cycle(selector)
    if(node)new MutationObserver(updateQualityContext).observe(node,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['class']})
  }
  updateQualityContext()
}

function initOperationalCycle(){
  if(!cycleStage)return
  installCycleCss()
  installCycleRail()
  installRadarState()
  installStrategyState()
  installQualityState()
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initOperationalCycle,{once:true})
else initOperationalCycle()
