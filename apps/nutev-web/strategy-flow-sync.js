import './i18n.js'

function flowApi(){return window.NutEVStrategyFlow||null}
function text(selector){return String(document.querySelector(selector)?.textContent||'').trim()}
function currentStep(step){return flowApi()?.read?.()?.[step]||{}}
function sameValue(left,right){return JSON.stringify(left)===JSON.stringify(right)}

function publish(step,patch){
  const api=flowApi()
  if(!api?.update)return
  const current=currentStep(step)
  if(Object.entries(patch).every(([key,value])=>sameValue(current[key],value)))return
  api.update(step,patch)
}

function classificationProgress(){
  const match=text('#classificationCounter').match(/(\d+)\s*\/\s*(\d+)/)
  return match?{done:Number(match[1]),total:Number(match[2])}:{done:0,total:0}
}

function syncQa(){
  const badge=text('#qaSummary .qa-badge').toUpperCase()
  const runCard=text('#mainRunCard')
  if(badge){
    const progress=classificationProgress()
    publish('qa',{
      status:badge==='PASS'?'TECHNICAL_PASS':'REVIEW_REQUIRED',
      technical_gate:badge,
      scientific_decision:'PENDING_HUMAN_REVIEW',
      human_classifications_done:progress.done,
      human_classifications_total:progress.total
    })
    return
  }
  if(runCard.includes('Run principal elegível para QA')){
    publish('qa',{status:'READY',scientific_decision:'PENDING_HUMAN_REVIEW'})
  }else if(runCard.includes('Nenhum run compatível encontrado')){
    publish('qa',{status:'PENDING_RUN',scientific_decision:'PENDING_HUMAN_REVIEW'})
  }else if(runCard.includes('Run ainda não elegível')){
    publish('qa',{status:'REVIEW_REQUIRED',scientific_decision:'PENDING_HUMAN_REVIEW'})
  }
}

function syncPress(){
  const status=text('#pressStatus .status-pill')
  const decision=text('#pressSummary .press-decision')
  if(status||decision){
    let normalized='PRESS_IN_REVIEW'
    if(/complete|conclu/i.test(`${status} ${decision}`))normalized='PRESS_REVIEW_COMPLETE_PENDING_CANONICAL_REGISTRATION'
    else if(/fail|não aprovado|reprov/i.test(`${status} ${decision}`))normalized='PRESS_FAIL'
    else if(/revision|required|revis/i.test(`${status} ${decision}`))normalized='REVISION_REQUIRED'
    publish('press',{status:normalized,scientific_decision:'PENDING_CANONICAL_REGISTRATION'})
  }
}

function syncRegional(){
  const status=text('#regionalStatus .status-pill')
  const body=text('#regionalSummary')
  if(status||body){
    let normalized='READY_FOR_EVIDENCE'
    if(/pass|documentad|complet/i.test(`${status} ${body}`))normalized='PASS'
    else if(/review|required|incomplet|pend/i.test(`${status} ${body}`))normalized='REVIEW_REQUIRED'
    publish('regional',{status:normalized,scientific_decision:'PENDING_GF01_REGISTRATION'})
  }
}

function sync(){
  const path=location.pathname
  if(path.endsWith('/review-qa.html'))syncQa()
  if(path.endsWith('/press-review.html'))syncPress()
  if(path.endsWith('/regional-routes.html'))syncRegional()
}

sync()
new MutationObserver(sync).observe(document.body,{childList:true,subtree:true,characterData:true,attributes:true})