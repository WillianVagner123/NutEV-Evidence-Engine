const $=selector=>document.querySelector(selector)
const esc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')

const APPLICATION_LABELS={
  GENERIC_EVIDENCE_PROJECT:'Projeto de evidências',
  SCOPING_REVIEW:'Revisão de escopo',
  INTEGRATIVE_REVIEW:'Revisão integrativa'
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

function renderNoProject(context){
  $('#projectHealth').textContent='projeto necessário'
  $('#projectState').innerHTML=`<div class="empty-state"><strong>Selecione um projeto</strong><span>Use o seletor de contexto acima para escolher o projeto que deseja abrir. Nenhuma ação privada será executada sem esse contexto.</span></div>`
  $('#applicationPanel').classList.add('hidden')
  $('#templatePanel').classList.add('hidden')
  $('#projectModulesSection').classList.add('hidden')
}

function renderProjectIdentity(context,application){
  const current=context.current||{}
  const workspaceName=nameFor(context.workspaces,current.workspace_id)||'Workspace'
  const projectName=nameFor(context.projects,current.project_id)||'Projeto'
  const appLabel=application?applicationLabel(application.application_type):'Aplicação ainda não configurada'
  $('#projectState').innerHTML=`<div class="product-panel-head"><div class="project-identity"><div class="project-mark" aria-hidden="true">◇</div><div class="project-identity-copy"><strong>${esc(projectName)}</strong><span>${esc(workspaceName)} · ${esc(appLabel)}</span></div></div><span class="project-badge ${application?'':'neutral'}">${application?'Projeto ativo':'Configuração pendente'}</span></div><div class="product-actions"><a class="action-primary" href="/search.html">Buscar evidências</a><a class="action-secondary" href="/evidence-library.html">Abrir biblioteca</a><a class="action-secondary" href="/exports.html">Exportações</a></div>`
  $('#projectHealth').textContent=application?'contexto pronto':'configuração pendente'
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

function renderModules(application){
  const appType=String(application?.application_type||'')
  const reviewCopy=appType==='SCOPING_REVIEW'?'Triagem e verificação humana da revisão de escopo.':appType==='INTEGRATIVE_REVIEW'?'Triagem e verificação humana da revisão integrativa.':'Verificação humana configurável quando o projeto exigir.'
  const modules=[
    {href:'/search.html',icon:'⌕',title:'Buscar evidências',copy:'Consultar múltiplas fontes, normalizar, deduplicar e priorizar resultados.',meta:'SEARCH → NORMALIZE → DEDUPLICATE → RANK'},
    {href:'/evidence-library.html',icon:'▤',title:'Biblioteca',copy:'Organizar documentos globais com estado, tags e notas privadas do projeto.',meta:'Identidade global · contexto privado'},
    {href:'/search.html?view=history',icon:'◷',title:'Minhas buscas',copy:'Reabrir buscas persistidas neste contexto sem executar novamente.',meta:'Histórico isolado por tenant'},
    {href:'/exports.html',icon:'⇩',title:'Exportações',copy:'Ver artefatos do projeto e a integridade da trilha de auditoria.',meta:'Manifesto + cadeia auditável'},
    {href:'/advanced.html#reviews',icon:'✓',title:'Revisão humana',copy:reviewCopy,meta:'Decisões humanas permanecem explícitas'},
    {href:'/advanced.html',icon:'⚙',title:'Laboratório avançado',copy:'Acessar PRESS, QA, síntese e módulos metodológicos quando realmente necessários.',meta:'Fora do fluxo principal'}
  ]
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

async function init(){
  try{
    const context=await jsonFetch('/api/context')
    if(!context.current?.project_id){renderNoProject(context);return}
    const [applicationPayload,templatesPayload]=await Promise.all([jsonFetch('/api/application'),jsonFetch('/api/application/templates')])
    const application=applicationPayload.application||null
    const templates=Array.isArray(templatesPayload.templates)?templatesPayload.templates:[]
    renderProjectIdentity(context,application)
    if(application){renderApplication(application,templates);renderModules(application)}
    else{renderTemplates(templates);renderModules(null)}
  }catch(error){
    if(error.status===401)return
    $('#projectHealth').textContent='indisponível'
    $('#projectState').innerHTML=`<div class="empty-state"><strong>Não foi possível abrir o projeto</strong><span>${error.status===403?'Seu papel não permite acessar este projeto.':'O contexto ou a aplicação está temporariamente indisponível.'}</span></div>`
  }
}

$('#configureApplication')?.addEventListener('click',configureApplication)
init()
