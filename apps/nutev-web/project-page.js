const $=selector=>document.querySelector(selector)
const esc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')

const APPLICATION_LABELS={
  GENERIC_EVIDENCE_PROJECT:'Projeto de evidências',
  SCOPING_REVIEW:'Revisão de escopo',
  INTEGRATIVE_REVIEW:'Revisão integrativa'
}
// Capabilities mirror ROLE_PERMISSIONS in src/nutev/tenancy/permissions.py. They decide what
// the page renders, never what is allowed: the server re-authorizes every request. Rendering a
// control the role cannot use would only produce a 403 on click, so forbidden actions are simply
// not drawn.
const ROLE_CAPABILITIES={
  WORKSPACE_OWNER:{search:true,libraryWrite:true,review:true,applicationManage:true,membersManage:true,exports:true,advanced:true},
  WORKSPACE_ADMIN:{search:true,libraryWrite:true,review:true,applicationManage:true,membersManage:true,exports:true,advanced:true},
  RESEARCHER:{search:true,libraryWrite:true,review:true,applicationManage:true,membersManage:false,exports:true,advanced:true},
  VIEWER:{search:false,libraryWrite:false,review:false,applicationManage:false,membersManage:false,exports:true,advanced:false},
  ACADEMIC_SUPERVISOR:{search:false,libraryWrite:false,review:false,applicationManage:false,membersManage:false,exports:true,advanced:false},
  REVIEWER:{search:false,libraryWrite:false,review:true,applicationManage:false,membersManage:false,exports:false,advanced:false},
  GUEST_REVIEWER:{search:false,libraryWrite:false,review:true,applicationManage:false,membersManage:false,exports:false,advanced:false}
}
const NO_CAPABILITIES={search:false,libraryWrite:false,review:false,applicationManage:false,membersManage:false,exports:false,advanced:false}
const ROLE_LABELS={
  WORKSPACE_OWNER:'Proprietário',
  WORKSPACE_ADMIN:'Administrador',
  RESEARCHER:'Pesquisador',
  REVIEWER:'Revisor',
  VIEWER:'Visualizador',
  ACADEMIC_SUPERVISOR:'Professor orientador',
  GUEST_REVIEWER:'Revisor convidado'
}
const GATE_LABELS={
  discovery:'Discovery',
  press:'PRESS',
  gf10:'GF-10',
  query_freeze:'Congelamento de consulta',
  formal_search:'Busca formal',
  prisma:'PRISMA formal'
}
const GATE_STATE_LABELS={
  COMPLETE:'Concluído',
  PENDING:'Pendente',
  PASS:'Aprovado',
  AUTHORIZED:'Autorizado',
  NOT_AUTHORIZED:'Não autorizado',
  EXECUTED:'Executada',
  NOT_EXECUTED:'Não executada',
  CREATED:'Criado',
  NOT_CREATED:'Não criado'
}
const GATE_NOTES={
  discovery:'Descoberta/harvest técnico concluído. Não é busca formal nem contagem PRISMA.',
  press:'O registro PRESS ainda não foi marcado como aprovado.',
  gf10:'A autorização GF-10 não foi concedida.',
  query_freeze:'As consultas por provedor ainda não foram congeladas com checksum.',
  formal_search:'A busca formal de revisão sistemática ainda não foi executada.',
  prisma:'Nenhum evento de busca PRISMA foi emitido.'
}
const COMPONENT_LABELS={
  RESEARCH_QUESTION:'Pergunta de pesquisa',PCC:'PCC',SEARCH:'Busca',NORMALIZE:'Normalização',TRACEABILITY:'Rastreabilidade',DEDUPLICATE:'Deduplicação',DEDUPLICATION:'Deduplicação',ORGANIZE:'Organização',TITLE_ABSTRACT_SCREENING:'Triagem título/resumo',FULL_TEXT:'Texto completo',EXTRACTION:'Extração',HUMAN_VERIFICATION:'Verificação humana',SYNTHESIS:'Síntese',PRISMA_SCR:'PRISMA-ScR'
}

async function jsonFetch(url,options={}){
  const response=await fetch(url,{cache:'no-store',credentials:'same-origin',...options})
  let payload={}
  try{payload=await response.json()}catch{}
  if(!response.ok){const error=new Error(payload?.error||`http_${response.status}`);error.status=response.status;error.payload=payload;throw error}
  return payload
}

function nameFor(items,id){return(items||[]).find(item=>item.id===id)?.name||''}
function applicationLabel(value){return APPLICATION_LABELS[String(value||'')]||String(value||'Aplicação personalizada').replaceAll('_',' ').toLocaleLowerCase('pt-BR')}
function componentLabel(value){return COMPONENT_LABELS[String(value||'')]||String(value||'').replaceAll('_',' ').toLocaleLowerCase('pt-BR')}

function renderLegacy(){
  $('#projectHealth').textContent='modo legado'
  $('#projectState').innerHTML='<div class="empty-state"><strong>Projetos multi-tenant não estão ativos neste runtime</strong><span>O modo legado mantém a experiência local de busca e Workbench. Workspaces, projetos e aplicações de pesquisa ficam disponíveis no modo autenticado.</span></div>'
  $('#applicationPanel').classList.add('hidden')
  $('#templatePanel').classList.add('hidden')
  $('#projectModulesSection').classList.add('hidden')
  $('#scientificStatePanel').classList.add('hidden')
  $('#adminSection').classList.add('hidden')
}

function renderNoProject(context){
  const workspaces=Array.isArray(context.workspaces)?context.workspaces:[]
  const projects=Array.isArray(context.projects)?context.projects:[]
  const current=context.current||{}
  $('#projectHealth').textContent='projeto necessário'
  if(!workspaces.length){
    $('#projectState').innerHTML='<div class="empty-state"><strong>Acesso ainda não provisionado</strong><span>Seu login está ativo, mas nenhum workspace foi atribuído à sua conta. Um administrador do NutEV precisa criar ou liberar seu espaço de pesquisa antes do primeiro projeto.</span></div>'
  }else if(current.workspace_id&&!projects.length){
    $('#projectState').innerHTML='<div class="empty-state"><strong>Nenhum projeto disponível neste workspace</strong><span>Seu acesso ao workspace está ativo. Peça ao proprietário ou administrador que crie ou libere o projeto de pesquisa.</span></div>'
  }else{
    $('#projectState').innerHTML='<div class="empty-state"><strong>Selecione um projeto</strong><span>Use o seletor de contexto acima para escolher o projeto. Busca, biblioteca, revisão e exportação só serão executadas depois dessa escolha.</span></div>'
  }
  $('#applicationPanel').classList.add('hidden')
  $('#templatePanel').classList.add('hidden')
  $('#projectModulesSection').classList.add('hidden')
  $('#scientificStatePanel').classList.add('hidden')
  $('#adminSection').classList.add('hidden')
}

function renderProjectIdentity(context,application,capabilities,role){
  const current=context.current||{}
  const workspaceName=nameFor(context.workspaces,current.workspace_id)||'Workspace'
  const projectName=nameFor(context.projects,current.project_id)||'Projeto'
  const appLabel=application?applicationLabel(application.application_type):'Aplicação ainda não configurada'
  const roleName=ROLE_LABELS[String(role||'')]||''
  const actions=[
    capabilities.search?'<a class="action-primary" href="/search.html">Buscar evidências</a>':'',
    '<a class="action-secondary" href="/evidence-library.html">Abrir biblioteca</a>',
    capabilities.review?'<a class="action-secondary" href="/review.html">Revisão humana</a>':'',
    capabilities.exports?'<a class="action-secondary" href="/exports.html">Exportações</a>':''
  ].filter(Boolean).join('')
  const subtitle=[workspaceName,appLabel,roleName].filter(Boolean).join(' · ')
  $('#projectState').innerHTML=`<div class="product-panel-head"><div class="project-identity"><div class="project-mark" aria-hidden="true">◇</div><div class="project-identity-copy"><strong>${esc(projectName)}</strong><span>${esc(subtitle)}</span></div></div><span class="project-badge ${application?'':'neutral'}">${application?'Contexto configurado':'Configuração pendente'}</span></div><div class="product-actions">${actions}</div>`
  $('#projectHealth').textContent=application?'contexto configurado':'configuração pendente'
}

function gateStateLabel(gate){
  return GATE_STATE_LABELS[String(gate.state||'')]||String(gate.state||'')
}

function renderScientificState(state){
  if(!state){$('#scientificStatePanel').classList.add('hidden');return}
  const gates=Array.isArray(state.gates)?state.gates:[]
  $('#gateGrid').innerHTML=gates.map(gate=>{
    const label=GATE_LABELS[String(gate.key||'')]||String(gate.key||'')
    const note=GATE_NOTES[String(gate.key||'')]||''
    return `<div class="gate-card${gate.open?' is-open':''}"><strong>${esc(label)}</strong><span class="gate-state">${esc(gateStateLabel(gate))}</span><span class="gate-note">${esc(note)}</span></div>`
  }).join('')
  const pending=gates.filter(gate=>!gate.open).length
  $('#scientificStateBadge').textContent=pending?`${pending} portão(ões) em aberto`:'Portões concluídos'
  $('#scientificStateSummary').textContent=state.question
    ?'Situação atual dos portões metodológicos, lida da fonte canônica do Artigo 1.'
    :'Situação atual dos portões metodológicos do Artigo 1.'
  const corpus=state.discovery_corpus||{}
  const binding=state.historical_binding||{}
  const rows=[
    ['Corpus de descoberta',`${corpus.unique_references??'—'} referências únicas · ${corpus.accepted_structural_records??'—'} aceitas estruturalmente · ${corpus.structurally_quarantined_records??'—'} em quarentena estrutural`],
    ['Aprofundamento Tier A',`${corpus.tier_a_retrieved_or_partial??'—'} de ${corpus.tier_a_records??'—'} documentos recuperados ou parciais`],
    ['Natureza dos números','Contagens de descoberta e recuperação. Não são contagens PRISMA, triagem, inclusão nem exclusão.'],
    ['Vínculo histórico',`${binding.state==='ACTIVE'?'Ativo':'Não ativado'} — vínculo de acesso ao material histórico do Artigo 1. Não adota decisões científicas, de triagem ou PRISMA para este projeto.`],
    ['Fonte',String(state.source||'')]
  ]
  $('#scientificStateDetail').innerHTML=rows.map(([label,value])=>`<div><strong>${esc(label)}</strong><pre>${esc(value)}</pre></div>`).join('')
  $('#scientificStatePanel').classList.remove('hidden')
}

function renderApplication(application,templates){
  const template=(templates||[]).find(item=>item.template_id===application.template_id&&(!application.template_version||item.version===application.template_version))||null
  $('#applicationPanel').classList.remove('hidden')
  $('#templatePanel').classList.add('hidden')
  $('#applicationTitle').textContent=applicationLabel(application.application_type)
  $('#applicationDescription').textContent=template?.description||'Configuração metodológica privada deste projeto.'
  $('#applicationStatus').textContent=application.status==='archived'?'Arquivada':'Ativa'
  $('#applicationStatus').classList.toggle('neutral',application.status==='archived')
  const components=template?.components||[]
  $('#applicationComponents').innerHTML=components.length?components.map(item=>`<span class="component-chip">${esc(componentLabel(item))}</span>`).join(''):'<span class="small-state">Componentes definidos pela configuração do projeto.</span>'
  const configuration=application.configuration&&typeof application.configuration==='object'?application.configuration:{}
  const details=[
    ['ID da aplicação',application.id],
    ['Tipo',application.application_type],
    ['Template',application.template_id?`${application.template_id}@${application.template_version||'—'}`:'Personalizado'],
    ['Versão da configuração',application.config_version],
    ['Configuração privada',Object.keys(configuration).length?JSON.stringify(configuration,null,2):'Sem campos adicionais']
  ]
  $('#applicationTechnical').innerHTML=details.map(([label,value])=>`<div><strong>${esc(label)}</strong><pre>${esc(value||'—')}</pre></div>`).join('')
}

function renderModules(application,capabilities){
  const appType=String(application?.application_type||'')
  const reviewCopy=appType==='SCOPING_REVIEW'?'Triagem e verificação humana da revisão de escopo.':appType==='INTEGRATIVE_REVIEW'?'Triagem e verificação humana da revisão integrativa.':'Verificação humana configurável quando o projeto exigir.'
  const modules=[
    capabilities.search?{href:'/search.html',icon:'⌕',title:'Buscar evidências',copy:'Consultar múltiplas fontes, normalizar, deduplicar e priorizar resultados.',meta:'SEARCH → NORMALIZE → DEDUPLICATE → RANK'}:null,
    {href:'/evidence-library.html',icon:'▤',title:'Biblioteca',copy:capabilities.libraryWrite?'Organizar documentos globais com estado, tags e notas privadas do projeto.':'Consultar os documentos do projeto, com estado, tags e notas em leitura.',meta:'Identidade global · contexto privado'},
    {href:'/search.html?view=history',icon:'◷',title:capabilities.search?'Minhas buscas':'Histórico de buscas',copy:'Reabrir buscas persistidas neste contexto sem executar novamente.',meta:'Histórico isolado por tenant'},
    capabilities.exports?{href:'/exports.html',icon:'⇩',title:'Exportações',copy:'Ver artefatos do projeto e a integridade da trilha de auditoria.',meta:'Manifesto + cadeia auditável'}:null,
    {href:'/review.html',icon:'✓',title:capabilities.review?'Revisão humana':'Revisão humana (leitura)',copy:capabilities.review?reviewCopy:'Acompanhar rounds, pendências e o estado da adjudicação sem alterar decisões.',meta:'Rounds isolados por aplicação · decisões humanas explícitas'},
    capabilities.advanced?{href:'/advanced.html',icon:'⚙',title:'Laboratório avançado',copy:'Acessar PRESS, QA, síntese e módulos metodológicos quando realmente necessários.',meta:'Fora do fluxo principal'}:null
  ].filter(Boolean)
  $('#projectModules').innerHTML=modules.map(item=>`<a class="module-card" href="${item.href}"><span class="module-icon" aria-hidden="true">${item.icon}</span><strong>${esc(item.title)}</strong><span>${esc(item.copy)}</span><div class="module-meta">${esc(item.meta)}</div></a>`).join('')
  $('#projectModulesSection').classList.remove('hidden')
}

function renderTemplates(templates){
  $('#applicationPanel').classList.add('hidden')
  $('#templatePanel').classList.remove('hidden')
  const root=$('#templateGrid')
  root.innerHTML=(templates||[]).map((template,index)=>`<label class="template-option"><input type="radio" name="applicationTemplate" value="${esc(template.template_id)}" data-version="${esc(template.version)}" ${index===0?'checked':''}><strong>${esc(applicationLabel(template.application_type))}</strong><span>${esc(template.description||'Composição metodológica reutilizável.')}</span><div class="component-list">${(template.components||[]).slice(0,5).map(component=>`<span class="component-chip">${esc(componentLabel(component))}</span>`).join('')}${(template.components||[]).length>5?`<span class="component-chip">+${(template.components||[]).length-5}</span>`:''}</div></label>`).join('')
}

async function configureApplication(){
  const selected=document.querySelector('input[name="applicationTemplate"]:checked')
  const button=$('#configureApplication')
  const status=$('#configureStatus')
  if(!selected){status.textContent='Selecione uma aplicação.';return}
  button.disabled=true
  status.textContent='Configurando aplicação…'
  try{
    await jsonFetch('/api/application',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({template_id:selected.value,template_version:selected.dataset.version,config_version:'1',configuration:{}})})
    status.textContent='Aplicação configurada.'
    location.reload()
  }catch(error){
    status.textContent=error.status===403?'Seu papel não permite configurar a aplicação deste projeto.':error.status===404?'Template não encontrado. Atualize a página e tente novamente.':'Não foi possível configurar a aplicação.'
    button.disabled=false
  }
}

function currentRole(me,workspaceId){
  const membership=(me?.workspace_memberships||[]).find(item=>item.workspace_id===workspaceId&&item.status==='active')
  return membership?String(membership.role||''):''
}

async function optional(url){
  // The Article 1 gate state exists only for the pinned Article 1 project; every other
  // project legitimately gets not-found and simply renders without the panel.
  try{return await jsonFetch(url)}catch{return null}
}

async function init(){
  try{
    const auth=await jsonFetch('/api/auth/status')
    if(auth.mode!=='pilot'){renderLegacy();return}
    const context=await jsonFetch('/api/context')
    if(!context.current?.project_id){renderNoProject(context);return}
    const me=await optional('/api/auth/me')
    const role=currentRole(me,context.current.workspace_id)
    const capabilities=ROLE_CAPABILITIES[role]||NO_CAPABILITIES
    const [applicationPayload,templatesPayload,scientificState]=await Promise.all([
      jsonFetch('/api/application'),
      jsonFetch('/api/application/templates'),
      optional('/api/article1/scientific-state')
    ])
    const application=applicationPayload.application||null
    const templates=Array.isArray(templatesPayload.templates)?templatesPayload.templates:[]
    renderProjectIdentity(context,application,capabilities,role)
    renderScientificState(scientificState)
    if(capabilities.membersManage)$('#adminSection').classList.remove('hidden')
    if(application){renderApplication(application,templates);renderModules(application,capabilities)}
    else if(capabilities.applicationManage){renderTemplates(templates);renderModules(null,capabilities)}
    else{
      // Someone who cannot configure the application should see why the project looks empty
      // rather than a template picker whose submit the server would refuse.
      $('#applicationPanel').classList.add('hidden')
      $('#templatePanel').classList.add('hidden')
      renderModules(null,capabilities)
    }
  }catch(error){
    if(error.status===401)return
    $('#projectHealth').textContent='indisponível'
    $('#projectState').innerHTML=`<div class="empty-state"><strong>Não foi possível abrir o projeto</strong><span>${error.status===403?'Seu papel não permite acessar este projeto.':'O contexto ou a aplicação está temporariamente indisponível.'}</span></div>`
  }
}

$('#configureApplication')?.addEventListener('click',configureApplication)
init()