import './i18n.js'

const STATUS_LABELS={
  COMPLETE:'Concluída',
  COMPLETE_WITH_PROVIDER_GAPS:'Concluída, com lacunas em algumas fontes',
  COMPLETE_WITH_AUDIT_GAPS:'Concluída, com lacunas de auditoria',
  PREFLIGHT:'Pré-verificação',
  PILOT:'Piloto',
  DEVELOPMENT:'Desenvolvimento',
  SUPPLEMENTARY:'Suplementar',
  FORMAL:'Formal'
}

const GLOSSARY=[
  ['Sistema de Evidências Científicas','O NutEV organiza busca, inspeção, revisão e governança de evidências com rastreabilidade e limites científicos explícitos.','Scientific Evidence System','NutEV organizes evidence search, inspection, review, and governance with traceability and explicit scientific boundaries.'],
  ['Busca progressiva','Execução que consulta fontes em etapas e preserva o estado de cada fonte. Uma fonte indisponível não é tratada como zero resultados.','Progressive search','A staged search that preserves each source state. An unavailable source is not treated as zero results.'],
  ['Fonte','Serviço externo consultado pelo sistema, como PubMed, Europe PMC, OpenAlex, Crossref, DOAJ, SciELO ou LILACS/BVS.','Source','An external service queried by the system, such as PubMed, Europe PMC, OpenAlex, Crossref, DOAJ, SciELO, or LILACS/BVS.'],
  ['Deduplicação','Processo que consolida registros equivalentes vindos de fontes diferentes sem apagar a proveniência de origem.','Deduplication','The process that consolidates equivalent records from different sources without removing origin provenance.'],
  ['Ordenação de busca','Ordem de apresentação condicionada à consulta e à prioridade operacional. Não significa qualidade, certeza, importância clínica ou recomendação.','Search ranking','Query-conditioned presentation order and operational priority. It does not mean quality, certainty, clinical importance, or recommendation.'],
  ['Proveniência','Rastro que liga um registro à fonte, consulta, versão e contexto em que foi recuperado e processado.','Provenance','The trace linking a record to the source, query, version, and context in which it was retrieved and processed.'],
  ['Espaço de trabalho','Fronteira principal de acesso privado que reúne projetos e separa dados entre contextos de trabalho.','Workspace','The main private-access boundary that groups projects and separates data across work contexts.'],
  ['Projeto','Contexto de pesquisa autorizado dentro de um espaço de trabalho. Busca, biblioteca, revisão e exportação são executadas dentro desse contexto.','Project','An authorized research context inside a workspace. Search, library, review, and export run within that context.'],
  ['Aplicação de pesquisa','Configuração metodológica explícita do projeto, como revisão de escopo, revisão integrativa ou outro uso científico governado.','Research Application','The project’s explicit methodological configuration, such as a scoping review, integrative review, or another governed scientific use.'],
  ['Mapa de Evidências','Visualização estrutural do corpus verificado. Mostra distribuição e concentração; não mede força, qualidade ou certeza da evidência.','Evidence Map','A structural view of the verified corpus. It shows distribution and concentration; it does not measure evidence strength, quality, or certainty.'],
  ['Análise de Evidências','Camada de inspeção que organiza domínios, sinais, documentos e pacotes de resultados. Não toma decisão científica automaticamente.','Evidence Analysis','An inspection layer that organizes domains, signals, documents, and result bundles. It does not make scientific decisions automatically.'],
  ['Revisão Humana','Etapa em que uma pessoa registra julgamento explícito e rastreável. Decisões humanas permanecem separadas de sinais automatizados.','Human Review','The stage where a person records explicit, traceable judgment. Human decisions remain separate from automated signals.'],
  ['Revisão de Síntese','Registro humano de comparabilidade, convergência, divergência e justificativa entre achados. Não equivale a meta-análise nem a certeza da evidência.','Synthesis Review','A human record of comparability, convergence, divergence, and rationale across findings. It is not a meta-analysis or evidence-certainty rating.'],
  ['Consulta de Evidências','Consulta determinística do corpus verificado que mostra documentos de suporte e explica a correspondência. Consulta não significa inclusão.','Evidence Query','A deterministic query over the verified corpus that shows supporting documents and explains matching. A query does not mean inclusion.'],
  ['Contexto de Evidências','Camada somente leitura com estado, manifesto e resumos estruturados usados pelas operações do sistema. Não cria fatos ausentes nem decisões científicas.','Evidence Context','A read-only layer containing state, manifest, and structured summaries used by system operations. It does not create missing facts or scientific decisions.'],
  ['Pacote de Evidências','Artefato auditável com pergunta, recorte, documentos de suporte, contexto verificado e regras de análise.','Evidence Packet','An auditable artifact containing the question, slice, supporting documents, verified context, and analysis rules.'],
  ['Pacote de resultados','Estrutura materializada a partir de um documento para inspeção. Não equivale a uma EvidenceClaim aceita.','Result bundle','A structure materialized from a document for inspection. It is not an accepted EvidenceClaim.'],
  ['Pronto para inspeção','Indica que existe material estruturado disponível para leitura. Não significa elegibilidade, inclusão, qualidade ou certeza.','Ready for inspection','Indicates that structured material is available for inspection. It does not mean eligibility, inclusion, quality, or certainty.'],
  ['Texto completo','Conteúdo integral de um documento quando a recuperação e o uso são permitidos e estão disponíveis.','Full text','The complete document content when retrieval and use are permitted and available.'],
  ['Bloqueio por segurança','Regra em que o sistema impede uma operação quando falta uma verificação necessária para prosseguir com segurança.','Fail-closed safeguard','A rule that blocks an operation when a required verification is missing.'],
  ['Camada operacional','Classificação de prioridade de processamento do banco. Organiza trabalho; não representa hierarquia de qualidade científica.','Operational tier','A processing-priority classification for the evidence bank. It organizes work; it is not a scientific-quality hierarchy.'],
  ['Pontuação operacional','Valor usado para organizar a ordem de processamento ou leitura. Não é escore de qualidade da evidência.','Operational score','A value used to organize processing or reading order. It is not an evidence-quality score.'],
  ['EvidenceClaim','Identificador canônico de uma alegação científica aceita dentro do fluxo governado.','EvidenceClaim','Canonical identifier for a scientific claim accepted within the governed workflow.'],
  ['PRESS','Método de revisão por pares da estratégia de busca. Aprovação em PRESS não autoriza, sozinha, busca formal, PRISMA ou conclusão científica.','PRESS','Peer review method for search strategies. PRESS approval alone does not authorize formal search, PRISMA reporting, or a scientific conclusion.'],
  ['GF-10','Gate metodológico do fluxo formal de busca. Permanece independente de outras etapas.','GF-10','A methodological gate in the formal-search workflow. It remains independent from other stages.'],
  ['PRISMA','Referencial de relato de revisões sistemáticas. Navegação, mapa, consulta ou contagens do sistema não devem ser confundidos com PRISMA.','PRISMA','A reporting framework for systematic reviews. Navigation, mapping, querying, or system counts must not be confused with PRISMA.']
]

const STRATEGY_FLOW_STORAGE_KEY='nutev_strategy_flow:article1-scientific-closure-v1'
const STRATEGY_FLOW_KEYS=['qa','press','regional']
let runtimeMode='unknown'
let strategyFlowEnabled=false

function escapeHtml(value){
  return String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')
}

function productLanguage(){return window.NutEVI18n?.language==='en'?'en':'pt-BR'}
function localizedGlossaryEntry(entry){return productLanguage()==='en'?[entry[2],entry[3]]:[entry[0],entry[1]]}

function ensureProductStyles(){
  if(document.querySelector('link[data-nutev-product-ui]'))return
  const link=document.createElement('link')
  link.rel='stylesheet'
  link.href='/product-ui.css'
  link.dataset.nutevProductUi='true'
  document.head.appendChild(link)
}

function navGroups(){
  if(runtimeMode==='legacy')return[
    {label:'Descoberta',items:[
      {key:'dashboard',href:'/',icon:'⌂',label:'Início'},
      {key:'search',href:'/search.html',icon:'⌕',label:'Buscar artigos'},
      {key:'library',href:'/articles.html',icon:'▤',label:'Biblioteca'}
    ]},
    {label:'Sistema',items:[
      {key:'history',href:'/search.html?view=history',icon:'◷',label:'Minhas buscas'},
      {key:'advanced',href:'/advanced.html',icon:'⚙',label:'Laboratório avançado'}
    ]}
  ]
  return[
    {label:'Pesquisa',items:[
      {key:'dashboard',href:'/',icon:'⌂',label:'Início'},
      {key:'project',href:'/project.html',icon:'◇',label:'Projeto'},
      {key:'search',href:'/search.html',icon:'⌕',label:'Buscar evidências'},
      {key:'library',href:'/evidence-library.html',icon:'▤',label:'Biblioteca'},
      {key:'exports',href:'/exports.html',icon:'⇩',label:'Exportações'}
    ]},
    {label:'Atividade',items:[
      {key:'history',href:'/search.html?view=history',icon:'◷',label:'Minhas buscas'},
      {key:'advanced',href:'/advanced.html',icon:'⚙',label:'Laboratório avançado'}
    ]}
  ]
}

function activeNavKey(){
  const path=location.pathname.replace(/\/+$/,'')||'/'
  const params=new URLSearchParams(location.search)
  if(path==='/search.html'&&params.get('view')==='history')return 'history'
  if(path==='/')return 'dashboard'
  if(path==='/project.html')return 'project'
  if(path==='/search.html')return 'search'
  if(path==='/evidence-library.html'||path==='/articles.html')return 'library'
  if(path==='/exports.html')return 'exports'
  if(['/evidence.html','/evidence-map.html','/radar.html','/ask.html'].includes(path))return 'advanced'
  if(path==='/advanced.html')return 'advanced'
  if(path.startsWith('/validation')||[
    '/scientific-dashboard.html','/review.html','/review-routes.html','/review-qa.html',
    '/press-review.html','/regional-routes.html','/quality.html','/strategy.html',
    '/intelligence.html','/synthesis-review.html','/synthesis-brief.html',
    '/synthesis-governance.html','/synthesis-release.html','/synthesis-publication.html',
    '/evidence-claims.html','/claim-appraisal.html','/evidence-sets.html',
    '/recommendation-candidates.html','/recommendation-human-validation.html'
  ].includes(path))return 'advanced'
  return ''
}

function canonicalNavHtml(active){
  return navGroups().map(group=>{
    const items=group.items.map(item=>`<a class="nav-item${active===item.key?' active':''}" href="${item.href}"${active===item.key?' aria-current="page"':''}><span class="nav-icon" aria-hidden="true">${item.icon}</span><span>${escapeHtml(item.label)}</span></a>`).join('')
    return `<div class="nav-group-label">${escapeHtml(group.label)}</div>${items}`
  }).join('')
}

function normalizeNavigation(force=false){
  const active=activeNavKey()
  const signature=`v4:${runtimeMode}:${active}`
  document.querySelectorAll('.sidebar nav,.product-nav').forEach(nav=>{
    if(!force&&nav.dataset.nutevCanonicalNav===signature)return
    nav.setAttribute('aria-label','Navegação principal')
    if(!nav.id)nav.id='nutevPrimaryNavigation'
    nav.innerHTML=canonicalNavHtml(active)
    nav.dataset.nutevCanonicalNav=signature
  })
}

function ensureMobileNavToggle(){
  const sidebar=document.querySelector('.sidebar')
  const nav=sidebar?.querySelector('nav')
  if(!sidebar||!nav||sidebar.querySelector('.mobile-nav-toggle'))return
  if(!nav.id)nav.id='nutevPrimaryNavigation'
  const button=document.createElement('button')
  button.type='button'
  button.className='mobile-nav-toggle'
  button.setAttribute('aria-controls',nav.id)
  button.setAttribute('aria-expanded','false')
  button.setAttribute('aria-label','Abrir navegação')
  button.innerHTML='<span aria-hidden="true">☰</span><span class="mobile-nav-label">Menu</span>'
  const brand=sidebar.querySelector('.brand')
  if(brand)brand.insertAdjacentElement('afterend',button)
  else sidebar.prepend(button)
  button.addEventListener('click',()=>{
    const open=sidebar.classList.toggle('mobile-nav-open')
    button.setAttribute('aria-expanded',String(open))
    button.setAttribute('aria-label',open?'Fechar navegação':'Abrir navegação')
  })
  nav.addEventListener('click',event=>{
    if(!event.target.closest('a'))return
    sidebar.classList.remove('mobile-nav-open')
    button.setAttribute('aria-expanded','false')
    button.setAttribute('aria-label','Abrir navegação')
  })
}

function shouldTranslateNode(node){
  const parent=node.parentElement
  if(!parent)return false
  return !parent.closest('code,pre,script,style,textarea,[data-raw-enum]')
}

function translateInternalEnums(root=document){
  if(root.nodeType===Node.TEXT_NODE){
    if(!shouldTranslateNode(root))return
    let text=root.nodeValue||''
    for(const [raw,label] of Object.entries(STATUS_LABELS))text=text.replaceAll(raw,label)
    if(text!==root.nodeValue)root.nodeValue=text
    return
  }
  if(!(root instanceof Element||root===document))return
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT)
  const nodes=[]
  while(walker.nextNode())nodes.push(walker.currentNode)
  for(const node of nodes)translateInternalEnums(node)
}

function explainResultCap(){
  const summary=document.querySelector('#summary')
  const values=[...document.querySelectorAll('#summary .summary-grid .kpi strong')].map(node=>Number(String(node.textContent||'').replace(/\D/g,'')))
  if(!summary||values.length<3||!Number.isFinite(values[0])||!Number.isFinite(values[2]))return
  const unique=values[0],returned=values[2]
  let note=document.querySelector('#resultCapNote')
  if(unique<=returned){note?.remove();return}
  if(!note){note=document.createElement('div');note.id='resultCapNote';note.className='review-result-note';summary.appendChild(note)}
  const copy=`Exibindo ${returned.toLocaleString('pt-BR')} de ${unique.toLocaleString('pt-BR')} referências únicas. Este modo possui limite de apresentação; use a busca sem teto para recuperar o conjunto completo.`
  if(note.textContent!==copy)note.textContent=copy
}

function markStaticKpis(root=document){
  const scope=root instanceof Element?root:document
  scope.querySelectorAll?.('#summary .summary-grid .kpi,.summary-grid .kpi').forEach(kpi=>{
    kpi.classList.add('static-kpi')
    kpi.setAttribute('role','group')
    kpi.setAttribute('title','Indicador informativo; não abre detalhamento.')
  })
}

function ensureSkipLink(){
  if(document.querySelector('.skip-link'))return
  const target=document.querySelector('main.main,main,.workspace-body')
  if(!target)return
  if(!target.id)target.id='mainContent'
  const link=document.createElement('a')
  link.className='skip-link'
  link.href=`#${target.id}`
  link.textContent='Pular para o conteúdo principal'
  document.body.prepend(link)
}

function glossaryRows(filter=''){
  const normalized=filter.trim().toLocaleLowerCase(productLanguage()==='en'?'en':'pt-BR')
  const rows=GLOSSARY.map(localizedGlossaryEntry).filter(([term,definition])=>!normalized||`${term} ${definition}`.toLocaleLowerCase(productLanguage()==='en'?'en':'pt-BR').includes(normalized))
  if(!rows.length)return `<p class="glossary-empty">${productLanguage()==='en'?'No terms found.':'Nenhum termo encontrado.'}</p>`
  return rows.map(([term,definition])=>`<div class="glossary-row"><dt>${escapeHtml(term)}</dt><dd>${escapeHtml(definition)}</dd></div>`).join('')
}

function refreshGlossary(){
  const dialog=document.querySelector('#nutevGlossaryDialog')
  if(!dialog)return
  const english=productLanguage()==='en'
  const eyebrow=dialog.querySelector('.glossary-eyebrow')
  const title=dialog.querySelector('h2')
  const intro=dialog.querySelector('.glossary-head p')
  const label=dialog.querySelector('.glossary-search')
  const input=dialog.querySelector('#nutevGlossarySearch')
  const list=dialog.querySelector('#nutevGlossaryList')
  if(eyebrow)eyebrow.textContent=english?'How the system works':'Como o sistema funciona'
  if(title)title.textContent=english?'Scientific Evidence System Glossary':'Glossário do Sistema de Evidências'
  if(intro)intro.textContent=english?'Definitions of system functions, states, scientific boundaries, and governed artifacts.':'Definições das funções, estados, limites científicos e artefatos governados do sistema.'
  if(label){const textNode=[...label.childNodes].find(node=>node.nodeType===Node.TEXT_NODE);if(textNode)textNode.nodeValue=english?'Filter terms':'Filtrar termos'}
  if(input)input.placeholder=english?'E.g.: source, provenance, review, PRESS':'Ex.: fonte, proveniência, revisão, PRESS'
  if(list)list.innerHTML=glossaryRows(input?.value||'')
}

function ensureGlossary(){
  if(document.querySelector('#nutevGlossaryButton')||location.pathname==='/login.html')return
  const button=document.createElement('button')
  button.id='nutevGlossaryButton'
  button.className='glossary-trigger'
  button.type='button'
  button.textContent='Glossário'
  button.setAttribute('aria-haspopup','dialog')

  const dialog=document.createElement('dialog')
  dialog.id='nutevGlossaryDialog'
  dialog.className='glossary-dialog'
  dialog.innerHTML=`<div class="glossary-head"><div><span class="glossary-eyebrow"></span><h2></h2><p></p></div><button class="glossary-close" type="button" aria-label="Fechar glossário">×</button></div><label class="glossary-search">Filtrar termos<input id="nutevGlossarySearch" type="search" autocomplete="off"></label><dl id="nutevGlossaryList" class="glossary-list"></dl>`

  document.body.append(button,dialog)
  refreshGlossary()
  const close=()=>{if(typeof dialog.close==='function')dialog.close();else dialog.removeAttribute('open')}
  button.addEventListener('click',()=>{refreshGlossary();if(typeof dialog.showModal==='function')dialog.showModal();else dialog.setAttribute('open','')})
  dialog.querySelector('.glossary-close')?.addEventListener('click',close)
  dialog.addEventListener('click',event=>{if(event.target===dialog)close()})
  dialog.querySelector('#nutevGlossarySearch')?.addEventListener('input',event=>{
    const list=dialog.querySelector('#nutevGlossaryList')
    if(list)list.innerHTML=glossaryRows(event.target.value)
  })
}

function readStrategyFlowState(){
  if(!strategyFlowEnabled)return{}
  try{return JSON.parse(localStorage.getItem(STRATEGY_FLOW_STORAGE_KEY)||'{}')||{}}
  catch{return{}}
}

function updateStrategyFlowState(step,patch={}){
  if(!strategyFlowEnabled||!STRATEGY_FLOW_KEYS.includes(step))return null
  const current=readStrategyFlowState()
  const next={...current,[step]:{...(current[step]||{}),...patch,updated_at:new Date().toISOString()}}
  try{localStorage.setItem(STRATEGY_FLOW_STORAGE_KEY,JSON.stringify(next))}catch{}
  window.dispatchEvent(new CustomEvent('nutev:strategy-flow-update',{detail:{step,state:next}}))
  return next[step]
}

window.NutEVStrategyFlow={
  get key(){return strategyFlowEnabled?STRATEGY_FLOW_STORAGE_KEY:null},
  read:readStrategyFlowState,
  update:updateStrategyFlowState
}

function flowStatus(key,value={}){
  const status=String(value.status||'')
  if(key==='qa'){
    if(status==='TECHNICAL_PASS'){
      const done=Number(value.human_classifications_done||0),total=Number(value.human_classifications_total||0)
      return{tone:'done',label:total&&done>=total?'Controle técnico concluído · amostra classificada':'Controle técnico concluído · revisão humana pendente'}
    }
    if(status==='REVIEW_REQUIRED')return{tone:'warn',label:'revisão técnica necessária'}
    if(status==='READY')return{tone:'ready',label:'execução elegível · controle técnico ainda não executado'}
    if(status==='PENDING_RUN')return{tone:'pending',label:'aguardando execução elegível'}
    return{tone:'pending',label:'ainda não executado'}
  }
  if(key==='press'){
    if(status==='PRESS_REVIEW_COMPLETE_PENDING_CANONICAL_REGISTRATION')return{tone:'done',label:'parecer concluído · registro canônico pendente'}
    if(status==='REVISION_REQUIRED')return{tone:'warn',label:'alteração material · revisar estratégia'}
    if(status==='PRESS_FAIL')return{tone:'warn',label:'PRESS não aprovado'}
    if(status==='PRESS_IN_REVIEW')return{tone:'ready',label:'parecer humano em revisão'}
    if(status==='READY_FOR_HUMAN_REVIEW')return{tone:'ready',label:'pacote pronto para revisão humana'}
    return{tone:'pending',label:'revisão humana ainda não registrada'}
  }
  if(key==='regional'){
    if(status==='PASS')return{tone:'done',label:'rotas documentadas · GF-01 candidato'}
    if(status==='REVIEW_REQUIRED')return{tone:'warn',label:'evidência regional incompleta'}
    if(status==='READY_FOR_EVIDENCE')return{tone:'ready',label:'aguardando evidência das rotas oficiais'}
    return{tone:'pending',label:'rotas ainda não avaliadas'}
  }
  return{tone:'pending',label:'pendente'}
}

function decorateStrategyFlow(){
  const flow=document.querySelector('.strategy-flow')
  if(!flow)return
  if(!strategyFlowEnabled){
    flow.dataset.nutevLocalState='disabled'
    flow.querySelectorAll('.strategy-flow-state').forEach(node=>node.remove())
    return
  }
  flow.dataset.nutevLocalState='legacy-only'
  const state=readStrategyFlowState()
  const nodes=[...flow.children].slice(0,3)
  nodes.forEach((node,index)=>{
    const key=STRATEGY_FLOW_KEYS[index]
    const result=flowStatus(key,state[key]||{})
    let marker=node.querySelector('.strategy-flow-state')
    if(!marker){marker=document.createElement('em');marker.className='strategy-flow-state';node.appendChild(marker)}
    const markerClass=`strategy-flow-state ${result.tone}`
    if(marker.className!==markerClass)marker.className=markerClass
    if(marker.textContent!==result.label)marker.textContent=result.label
    const done=result.tone==='done'
    node.classList.toggle('done',done)
  })
}

function strategyGuideCopy(){
  const path=location.pathname.replace(/\/+$/,'')||'/'
  if(path==='/review-qa.html')return 'O controle técnico verifica execução, sentinelas e amostras. Aprovação técnica continua diferente de decisão científica humana.'
  if(path==='/press-review.html')return 'PRESS exige revisor humano independente. Parecer concluído continua diferente de GF-10, congelamento da consulta e PRISMA.'
  if(path==='/regional-routes.html')return 'GF-01 documenta as rotas técnicas regionais. Completar esta etapa não autoriza congelamento da consulta nem busca formal.'
  return ''
}

function ensureStrategyFlowGuide(){
  const flow=document.querySelector('.strategy-flow')
  if(!flow)return
  let guide=document.querySelector('#nutevStrategyFlowGuide')
  if(!guide){
    guide=document.createElement('div')
    guide.id='nutevStrategyFlowGuide'
    guide.className='strategy-flow-guide'
    flow.parentNode.insertBefore(guide,flow)
  }
  const copy=strategyGuideCopy()
  const tenantCopy=runtimeMode==='pilot'?' No modo autenticado, estados locais do navegador ficam desativados para evitar mistura entre projetos.':''
  const signature=`${runtimeMode}:${copy||'default'}`
  if(guide.dataset.nutevGuideSignature===signature)return
  guide.innerHTML=`<strong>Roteiro operacional, não atalho de gate.</strong><span>A sequência orienta o trabalho; os gates permanecem independentes e nenhuma etapa autoriza automaticamente a decisão científica seguinte.${copy?` ${escapeHtml(copy)}`:''}${tenantCopy}</span>`
  guide.dataset.nutevGuideSignature=signature
}

async function renderBuildIdentity(){
  try{
    const response=await fetch('/api/version',{cache:'no-store'})
    if(!response.ok)return
    const build=await response.json()
    const main=document.querySelector('main.main,.main,.workspace')
    if(!main||document.querySelector('#nutevBuildFooter'))return
    const footer=document.createElement('footer')
    footer.id='nutevBuildFooter'
    footer.className='product-footer'
    const commit=String(build.commit||'unknown')
    const shortCommit=commit==='unknown'?commit:commit.slice(0,12)
    const time=build.build_time&&build.build_time!=='unknown'?` · ${build.build_time}`:''
    footer.textContent=`NutEV · build ${shortCommit}${time}`
    main.appendChild(footer)
  }catch{}
}

function applyProductUi(root=document){
  normalizeNavigation()
  ensureMobileNavToggle()
  translateInternalEnums(root)
  explainResultCap()
  markStaticKpis(root)
  ensureSkipLink()
  ensureGlossary()
  ensureStrategyFlowGuide()
  decorateStrategyFlow()
}

async function initRuntimeMode(){
  try{
    const response=await fetch('/api/auth/status',{cache:'no-store',credentials:'same-origin'})
    if(!response.ok)throw new Error(`auth_status_${response.status}`)
    const payload=await response.json()
    runtimeMode=payload?.mode==='legacy'?'legacy':payload?.mode==='pilot'?'pilot':'unknown'
  }catch{
    runtimeMode='unknown'
  }
  strategyFlowEnabled=runtimeMode==='legacy'
  normalizeNavigation(true)
  ensureStrategyFlowGuide()
  decorateStrategyFlow()
  if(runtimeMode==='pilot'){
    if(location.pathname==='/articles.html'){
      const params=new URLSearchParams(location.search)
      const saved=params.get('saved')
      const suffix=saved?`?article=${encodeURIComponent(saved)}`:''
      location.replace(`/evidence-library.html${suffix}`)
      return
    }
    if(location.pathname!='/login.html')import('/workspace-context.js').catch(()=>{})
  }
  window.dispatchEvent(new CustomEvent('nutev:runtime-mode',{detail:{mode:runtimeMode}}))
}

ensureProductStyles()
applyProductUi()
renderBuildIdentity()
initRuntimeMode()

window.addEventListener('nutev:strategy-flow-update',()=>decorateStrategyFlow())
window.addEventListener('nutev:language-change',()=>{refreshGlossary();normalizeNavigation(true)})
window.addEventListener('storage',event=>{if(strategyFlowEnabled&&event.key===STRATEGY_FLOW_STORAGE_KEY)decorateStrategyFlow()})

const observer=new MutationObserver(mutations=>{
  let summaryChanged=false
  let strategyChanged=false
  for(const mutation of mutations){
    for(const node of mutation.addedNodes){
      translateInternalEnums(node)
      if(node.nodeType===Node.ELEMENT_NODE){
        const element=node
        markStaticKpis(element)
        if(element.matches?.('#summary,.summary-grid')||element.querySelector?.('#summary,.summary-grid'))summaryChanged=true
        if(element.matches?.('.strategy-flow')||element.querySelector?.('.strategy-flow'))strategyChanged=true
      }
    }
  }
  if(summaryChanged)explainResultCap()
  if(strategyChanged){ensureStrategyFlowGuide();decorateStrategyFlow()}
})
observer.observe(document.documentElement,{childList:true,subtree:true})