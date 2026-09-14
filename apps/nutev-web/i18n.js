const STORAGE_KEY='nutev_language'
const DEFAULT_LANGUAGE='pt-BR'
const ENGLISH_LANGUAGE='en'

const PAIRS=[
  ['Motor de Evidências','Evidence Engine'],
  ['Idioma','Language'],
  ['Português','Portuguese'],
  ['Inglês','English'],
  ['Navegação principal','Primary navigation'],
  ['Abrir navegação','Open navigation'],
  ['Fechar navegação','Close navigation'],
  ['Pular para o conteúdo principal','Skip to main content'],
  ['Descoberta','Discovery'],
  ['Pesquisa','Research'],
  ['Atividade','Activity'],
  ['Sistema','System'],
  ['Início','Home'],
  ['Projeto','Project'],
  ['Buscar artigos','Search articles'],
  ['Buscar evidências','Search evidence'],
  ['Biblioteca','Library'],
  ['Exportações','Exports'],
  ['Minhas buscas','My searches'],
  ['Laboratório avançado','Advanced lab'],
  ['Visão geral','Overview'],
  ['Painel','Dashboard'],
  ['Evidências','Evidence'],
  ['Buscar','Search'],
  ['Explorador de Evidências','Evidence Explorer'],
  ['Mapa de Evidências','Evidence Map'],
  ['Inteligência Científica','Scientific Intelligence'],
  ['Revisão de Síntese','Synthesis Review'],
  ['Resumo de Síntese','Synthesis Brief'],
  ['Pergunte ao NutEV','Ask NutEV'],
  ['Radar de Evidências','Evidence Radar'],
  ['Revisão','Review'],
  ['Controle de Revisão','Review Control'],
  ['Rotas de Revisão','Review Routes'],
  ['Estratégia','Strategy'],
  ['Laboratório de Estratégia','Strategy Lab'],
  ['Validação','Validation'],
  ['Validação científica','Scientific validation'],
  ['Observatório de Qualidade','Quality Observatory'],
  ['Execuções de busca','Search runs'],
  ['Contexto de IA','AI Context'],
  ['Revisão humana','Human review'],
  ['Resumo executivo','Executive brief'],
  ['Imprimir / PDF','Print / PDF'],
  ['Atualizar','Refresh'],
  ['Exportar JSON','Export JSON'],
  ['Carregando…','Loading…'],
  ['verificando…','checking…'],
  ['Todos','All'],
  ['Todas','All'],
  ['Limpar filtros','Clear filters'],
  ['Matriz','Matrix'],
  ['Rota','Route'],
  ['Linha do tempo','Timeline'],
  ['Domínio','Domain'],
  ['Tipo documental','Document type'],
  ['Domínio × tipo de documento','Domain × document type'],
  ['Domínio × rota','Domain × route'],
  ['Publicações ao longo do tempo','Publications over time'],
  ['Documentos selecionados','Selected documents'],
  ['Menor concentração','Lower concentration'],
  ['Maior concentração','Higher concentration'],
  ['Abrir no Explorador de Evidências →','Open in Evidence Explorer →'],
  ['Limite de interpretação científica','Scientific interpretation boundary'],
  ['Artigo 1 · mapa estrutural do Tier A','Article 1 · Tier A structural map'],
  ['SUPORTE À SÍNTESE · SEM CONCLUSÃO AUTOMÁTICA','SYNTHESIS SUPPORT · NOT AUTOMATED CONCLUSION'],
  ['Do corpus organizado para uma leitura científica navegável','From organized corpus to navigable scientific reading'],
  ['Síntese por domínio','Domain synthesis'],
  ['Candidatos a achados vinculados à fonte','Source-linked finding candidates'],
  ['Rótulos de desfecho recorrentes','Recurring outcome labels'],
  ['Fila de revisão de convergência / divergência','Convergence / divergence review queue'],
  ['Sinais de cobertura do corpus','Corpus coverage signals'],
  ['Nenhum domínio selecionado.','No domain selected.'],
  ['Abrir revisão humana →','Open human review →'],
  ['INTERPRETAÇÃO CIENTÍFICA · SOMENTE NAVEGAÇÃO','INTERPRETATION WORKFLOW · NAVIGATION ONLY'],
  ['Estruturar','Structure'],
  ['Inspecionar','Inspect'],
  ['Estruturar → Inspecionar → Revisão humana','Structure → Inspect → Human review'],
  ['Navegador de concentração por domínio','Domain concentration navigator'],
  ['volume ≠ força','volume ≠ strength'],
  ['Panorama de inspeção por domínio','Domain inspection panorama'],
  ['materializado ≠ alegação aceita','finding-ready ≠ accepted claim'],
  ['corpus mapeado','mapped corpus'],
  ['pronto para achado no domínio','finding-ready within domain'],
  ['Progresso de envio humano','Human submission progress'],
  ['envio ≠ resultado científico','submission ≠ scientific outcome'],
  ['Minha avaliação aberta','My open assessment'],
  ['CICLO OPERACIONAL DE PESQUISA','OPERATIONAL RESEARCH CYCLE'],
  ['Observar','Observe'],
  ['Preparar','Prepare'],
  ['Verificar','Verify'],
  ['Observar → Preparar → Verificar, sem promoção científica automática','Observe → Prepare → Verify, without automatic scientific promotion'],
  ['somente navegação','navigation only'],
  ['FLUXO CIENTÍFICO','SCIENTIFIC WORKFLOW'],
  ['Do mapa à decisão humana, sem atalhos científicos','From map to human decision, without scientific shortcuts'],
  ['ESPAÇO DE SÍNTESE DE PESQUISA','RESEARCH SYNTHESIS WORKSPACE'],
  ['Do julgamento humano à recuperação fundamentada — sem promoção automática','From human judgment to grounded retrieval — without automatic promotion'],
  ['Recuperação fundamentada','Grounded retrieval'],
  ['Provedor','Provider'],
  ['Ordenação','Ranking'],
  ['Espaço de trabalho','Workspace'],
  ['Glossário','Glossary'],
  ['Ajuda de termos','Terminology help'],
  ['Glossário científico','Scientific glossary'],
  ['Fechar glossário','Close glossary'],
  ['Filtrar termos','Filter terms'],
  ['Nenhum termo encontrado.','No terms found.'],
  ['Indicador informativo; não abre detalhamento.','Informational indicator; does not open details.'],
  ['Roteiro operacional, não atalho de gate.','Operational guide, not a gate shortcut.'],
  ['pendente','pending'],
  ['atribuído a mim','assigned to me'],
  ['Entrar','Sign in'],
  ['Entrar no NutEV','Sign in to NutEV'],
  ['E-mail','Email'],
  ['Senha','Password'],
  ['Voltar ao início','Back to home'],
  ['Seu trabalho científico, separado por projeto.','Your scientific work, separated by project.'],
  ['Use a conta provisionada para sua organização.','Use the account provisioned for your organization.'],
  ['Entrando…','Signing in…'],
  ['Informe e-mail e senha.','Enter email and password.'],
  ['Não foi possível verificar o serviço de autenticação. Tente novamente.','Could not verify the authentication service. Try again.'],
  ['Este ambiente está no modo legado e não oferece login de plataforma.','This environment is in legacy mode and does not provide platform sign-in.'],
  ['Acesso autenticado aos espaços de trabalho e projetos do NutEV Motor de Evidências.','Authenticated access to NutEV Evidence Engine workspaces and projects.'],
  ['Autenticação identifica a sessão. Permissões continuam sendo revalidadas no backend para cada espaço de trabalho, projeto e operação privada.','Authentication identifies the session. Permissions continue to be revalidated by the backend for each workspace, project, and private operation.'],
  ['Entre para acessar seus espaços de trabalho, pesquisas, biblioteca de evidências, aplicações metodológicas e exportações com isolamento de contexto.','Sign in to access your workspaces, research, evidence library, methodological applications, and exports with context isolation.'],
  ['Fonte externa consultada pelo NutEV, como PubMed, Europe PMC, OpenAlex, Crossref, DOAJ, SciELO ou LILACS/BVS.','External source queried by NutEV, such as PubMed, Europe PMC, OpenAlex, Crossref, DOAJ, SciELO, or LILACS/BVS.'],
  ['Ordem de apresentação condicionada à consulta, combinando relevância para a busca e prioridade operacional NutEV. Não significa qualidade, certeza ou recomendação.','Query-conditioned presentation order combining search relevance and NutEV operational priority. It does not mean quality, certainty, or recommendation.'],
  ['Espaço de trabalho que reúne projetos e define a fronteira principal de acesso privado.','Workspace that groups projects and defines the main private-access boundary.'],
  ['Projeto de pesquisa dentro de um espaço de trabalho. Busca, biblioteca, revisão e exportação são autorizadas novamente para esse contexto.','Research project inside a workspace. Search, library, review, and export are authorized again for that context.'],
  ['Definições da interface para reduzir ambiguidade sem alterar os contratos científicos internos.','Interface definitions that reduce ambiguity without changing internal scientific contracts.'],
  ['Ex.: ordenação, espaço de trabalho, proveniência','E.g.: ranking, workspace, provenance'],
  ['Nenhum documento mapeado pelo perfil atual','No documents mapped by the current profile'],
  ['Nenhum documento mapeado','No documents mapped'],
  ['lacuna de evidência','evidence gap'],
  ['texto completo','full text'],
  ['pacote de resultados','result bundle']
]

const EXACT=new Map()
for(const [pt,en] of PAIRS){
  EXACT.set(pt,{pt,en})
  EXACT.set(en,{pt,en})
}

const DYNAMIC_PATTERNS=[
  {
    pt:/^(\d+) mapeamentos$/,
    en:/^(\d+) mapped placements$/,
    toPt:match=>`${match[1]} mapeamentos`,
    toEn:match=>`${match[1]} mapped placements`
  },
  {
    pt:/^Rodada (\d+)$/,
    en:/^Round (\d+)$/,
    toPt:match=>`Rodada ${match[1]}`,
    toEn:match=>`Round ${match[1]}`
  },
  {
    pt:/^(\d+)\/(\d+) itens com decisão salva$/,
    en:/^(\d+)\/(\d+) items with a saved decision$/,
    toPt:match=>`${match[1]}/${match[2]} itens com decisão salva`,
    toEn:match=>`${match[1]}/${match[2]} items with a saved decision`
  },
  {
    pt:/^(\d+)\/(\d+) revisores enviaram e travaram a própria avaliação$/,
    en:/^(\d+)\/(\d+) reviewers submitted and locked their own assessment$/,
    toPt:match=>`${match[1]}/${match[2]} revisores enviaram e travaram a própria avaliação`,
    toEn:match=>`${match[1]}/${match[2]} reviewers submitted and locked their own assessment`
  }
]

const SKIP_SELECTOR='script,style,code,pre,textarea,[data-raw-enum],[data-i18n-skip],[data-nutev-no-translate],.article-title,[data-article-title],.abstract,[data-abstract],.source-title,[data-source-title]'
const ATTRIBUTES=['placeholder','title','aria-label','aria-description']
let currentLanguage=DEFAULT_LANGUAGE

function normalizeLanguage(value){
  const raw=String(value||'').trim().toLowerCase()
  if(raw==='en'||raw==='en-us'||raw==='en-gb')return ENGLISH_LANGUAGE
  if(raw==='pt'||raw==='pt-br')return DEFAULT_LANGUAGE
  return null
}

function storedLanguage(){
  const query=normalizeLanguage(new URLSearchParams(location.search).get('lang'))
  if(query)return query
  try{return normalizeLanguage(localStorage.getItem(STORAGE_KEY))||DEFAULT_LANGUAGE}catch{return DEFAULT_LANGUAGE}
}

function preserveWhitespace(source,replacement){
  const leading=source.match(/^\s*/)?.[0]||''
  const trailing=source.match(/\s*$/)?.[0]||''
  return `${leading}${replacement}${trailing}`
}

function translateCore(core,language=currentLanguage){
  const entry=EXACT.get(core)
  if(entry)return language===ENGLISH_LANGUAGE?entry.en:entry.pt
  for(const pattern of DYNAMIC_PATTERNS){
    const matchPt=core.match(pattern.pt)
    const matchEn=core.match(pattern.en)
    const match=matchPt||matchEn
    if(match)return language===ENGLISH_LANGUAGE?pattern.toEn(match):pattern.toPt(match)
  }
  return core
}

function translateValue(value,language=currentLanguage){
  const source=String(value??'')
  const core=source.trim()
  if(!core)return source
  const translated=translateCore(core,language)
  return translated===core?source:preserveWhitespace(source,translated)
}

function shouldSkip(node){
  const element=node.nodeType===Node.ELEMENT_NODE?node:node.parentElement
  return Boolean(element?.closest?.(SKIP_SELECTOR))
}

function translateTextNode(node){
  if(node.nodeType!==Node.TEXT_NODE||shouldSkip(node))return
  const next=translateValue(node.nodeValue)
  if(next!==node.nodeValue)node.nodeValue=next
}

function translateAttributes(element){
  if(!(element instanceof Element)||shouldSkip(element))return
  for(const attribute of ATTRIBUTES){
    if(!element.hasAttribute(attribute))continue
    const source=element.getAttribute(attribute)
    const next=translateValue(source)
    if(next!==source)element.setAttribute(attribute,next)
  }
}

function translateTree(root=document){
  if(root.nodeType===Node.TEXT_NODE){translateTextNode(root);return}
  if(!(root instanceof Element||root===document))return
  if(root instanceof Element)translateAttributes(root)
  const textWalker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT)
  while(textWalker.nextNode())translateTextNode(textWalker.currentNode)
  const elementWalker=document.createTreeWalker(root,NodeFilter.SHOW_ELEMENT)
  while(elementWalker.nextNode())translateAttributes(elementWalker.currentNode)
}

function ensureStyles(){
  if(document.querySelector('link[data-nutev-i18n]'))return
  const link=document.createElement('link')
  link.rel='stylesheet'
  link.href='/i18n.css'
  link.dataset.nutevI18n='true'
  document.head.appendChild(link)
}

function updateSwitcher(){
  const switcher=document.querySelector('#nutevLanguageSwitch')
  if(!switcher)return
  switcher.setAttribute('aria-label',currentLanguage===ENGLISH_LANGUAGE?'Language':'Idioma')
  const label=switcher.querySelector('.nutev-language-switch-label')
  if(label)label.textContent=currentLanguage===ENGLISH_LANGUAGE?'Language':'Idioma'
  switcher.querySelectorAll('[data-nutev-language]').forEach(button=>{
    const active=button.dataset.nutevLanguage===currentLanguage
    button.setAttribute('aria-pressed',String(active))
    button.title=button.dataset.nutevLanguage===ENGLISH_LANGUAGE?(currentLanguage===ENGLISH_LANGUAGE?'English':'Inglês'):(currentLanguage===ENGLISH_LANGUAGE?'Portuguese':'Português')
  })
}

function ensureSwitcher(){
  if(document.querySelector('#nutevLanguageSwitch')){updateSwitcher();return}
  const switcher=document.createElement('div')
  switcher.id='nutevLanguageSwitch'
  switcher.className='nutev-language-switch'
  switcher.setAttribute('role','group')
  switcher.innerHTML='<span class="nutev-language-switch-label">Idioma</span><button type="button" data-nutev-language="pt-BR" aria-pressed="false">PT</button><button type="button" data-nutev-language="en" aria-pressed="false">EN</button>'
  switcher.addEventListener('click',event=>{
    const button=event.target.closest('[data-nutev-language]')
    if(!button)return
    setLanguage(button.dataset.nutevLanguage)
  })
  const sidebar=document.querySelector('.sidebar')
  if(sidebar){
    const brand=sidebar.querySelector('.brand')
    if(brand)brand.insertAdjacentElement('afterend',switcher)
    else sidebar.prepend(switcher)
  }else document.body.appendChild(switcher)
  updateSwitcher()
}

function applyLanguage(language=currentLanguage,{persist=false,announce=false}={}){
  currentLanguage=normalizeLanguage(language)||DEFAULT_LANGUAGE
  document.documentElement.lang=currentLanguage===ENGLISH_LANGUAGE?'en':'pt-BR'
  if(persist){try{localStorage.setItem(STORAGE_KEY,currentLanguage)}catch{}}
  ensureStyles()
  ensureSwitcher()
  translateTree(document)
  updateSwitcher()
  if(announce)window.dispatchEvent(new CustomEvent('nutev:language-change',{detail:{language:currentLanguage}}))
  return currentLanguage
}

function setLanguage(language){
  const next=normalizeLanguage(language)||DEFAULT_LANGUAGE
  if(next===currentLanguage){applyLanguage(next,{persist:true});return}
  applyLanguage(next,{persist:true,announce:true})
}

function t(pt,en){
  return currentLanguage===ENGLISH_LANGUAGE?en:pt
}

currentLanguage=storedLanguage()
applyLanguage(currentLanguage)

const observer=new MutationObserver(mutations=>{
  for(const mutation of mutations){
    if(mutation.type==='characterData')translateTextNode(mutation.target)
    for(const node of mutation.addedNodes)translateTree(node)
  }
})
observer.observe(document.documentElement,{childList:true,subtree:true,characterData:true})

window.addEventListener('storage',event=>{
  if(event.key!==STORAGE_KEY)return
  applyLanguage(normalizeLanguage(event.newValue)||DEFAULT_LANGUAGE,{announce:true})
})

window.NutEVI18n={
  get language(){return currentLanguage},
  setLanguage,
  translate:translateValue,
  t,
  languages:['pt-BR','en']
}

export {applyLanguage,setLanguage,t,translateTree,translateValue}
