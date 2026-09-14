const STORAGE_KEY='nutev_language'
const DEFAULT_LANGUAGE='pt-BR'
const ENGLISH_LANGUAGE='en'

// [Portuguese, English, optional aliases already present in legacy/mixed UI]
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
  ['Corpus','Corpus'],
  ['Governança','Governance'],
  ['Alegações científicas','Scientific claims'],
  ['Ferramentas de evidência','Evidence tools'],
  ['Explorador de Evidências','Evidence Explorer'],
  ['Mapa de Evidências','Evidence Map'],
  ['Inteligência Científica','Scientific Intelligence'],
  ['Revisão de Síntese','Synthesis Review'],
  ['Resumo de Síntese','Synthesis Brief'],
  ['Revisão Humana de Síntese','Human Synthesis Review'],
  ['Resumo de Síntese Verificado','Verified Synthesis Brief'],
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
  ['DOMÍNIO × FORMATO DOCUMENTAL · SEM RANKING','DOMAIN × DOCUMENT SHAPE · RANK-BLIND'],
  ['Síntese por domínio · achados candidatos · filas de comparação humana','Domain synthesis · finding candidates · human comparison queues'],
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
  ['Aguardando a matriz estrutural verificada.','Waiting for the verified structural matrix.'],
  ['Contagens estruturais do mapa atual. Clique para aplicar/remover o filtro de domínio existente.','Structural counts from the current map. Click to apply/remove the existing domain filter.'],
  ['Uma mesma referência pode contribuir para mais de um domínio. Concentração e célula vazia não representam qualidade, certeza, ausência de literatura ou lacuna de evidência.','The same reference may contribute to more than one domain. Concentration and empty cells do not represent quality, certainty, absence of literature, or an evidence gap.',['Uma mesma referência pode contribuir para mais de um domínio. Concentração e célula vazia não representam qualidade, certeza, ausência de literatura ou evidence gap.']],
  ['Aguardando a síntese estrutural sem ranking.','Waiting for the rank-blind structural synthesis.',['Aguardando a síntese estrutural rank-blind.']],
  ['Documentos mapeados e materialização de pacotes de resultados para inspeção.','Mapped documents and result-bundle materialization for inspection.',['Documentos mapeados e materialização de result bundles para inspeção.']],
  ['Disponibilidade técnica de pacote de resultados','Technical result-bundle availability'],
  ['Disponibilidade técnica de pacote de resultados não significa força, convergência, certeza, elegibilidade nem EvidenceClaim aceito.','Technical result-bundle availability does not mean strength, convergence, certainty, eligibility, or an accepted EvidenceClaim.',['Finding-ready descreve disponibilidade técnica de result bundle. Não significa força, convergência, certeza, elegibilidade nem EvidenceClaim aceito.']],
  ['Progresso de envio por rodada explicitamente vinculada à aplicação atual.','Submission progress by round explicitly bound to the current application.'],
  ['A barra mede somente submissão humana registrada. Ela não calcula inclusão, concordância, adjudicação científica, risco de viés, certeza ou PRISMA.','The bar measures only registered human submission. It does not calculate inclusion, agreement, scientific adjudication, risk of bias, certainty, or PRISMA.'],
  ['Nenhuma rodada explícita desta Aplicação de Pesquisa para visualizar. O painel não importa rodadas legadas nem infere vínculos.','No explicit round from this Research Application to display. The panel does not import legacy rounds or infer bindings.',['Nenhum round explícito desta ResearchApplication para visualizar. O painel não importa rounds legados nem infere bindings.']],
  ['CICLO OPERACIONAL DE PESQUISA','OPERATIONAL RESEARCH CYCLE'],
  ['Observar','Observe'],
  ['Preparar','Prepare'],
  ['Verificar','Verify'],
  ['Observe cobertura, lacunas e mudanças','Observe coverage, gaps and change'],
  ['Prepare decisões pré-PRESS','Prepare pre-PRESS decisions'],
  ['Verifique a integridade operacional','Verify operational integrity'],
  ['Observar → Preparar → Verificar, sem promoção científica automática','Observe → Prepare → Verify, without automatic scientific promotion',['Observe → Prepare → Verify, sem promoção científica automática']],
  ['somente navegação','navigation only'],
  ['Ciclo operacional de pesquisa','Operational research cycle'],
  ['Estado operacional do Radar','Radar operational state'],
  ['Tópicos com lacunas','Topics with gaps',['Tópicos com gaps']],
  ['Busca ativa requerida','Active search required'],
  ['Provedores observados','Observed providers',['Providers observados']],
  ['Lacunas técnicas','Technical gaps',['Gaps técnicos']],
  ['Busca ativa','Active search'],
  ['Provedores / Monitoramento','Providers / Watch',['Providers / Watch']],
  ['Atualizar Radar','Refresh Radar'],
  ['Ver monitoramento','View Watch',['Ver Watch']],
  ['Abrir Laboratório de Estratégia →','Open Strategy Lab →',['Abrir Strategy Lab →']],
  ['Estado operacional da Estratégia','Strategy operational state',['Estado operacional da Strategy']],
  ['rascunho','draft'],
  ['Congelamento da consulta','Query freeze'],
  ['Busca formal','Formal search'],
  ['Testes delta','Delta tests'],
  ['Abrir controle de qualidade','Open QA',['Abrir QA']],
  ['Abrir PRESS','Open PRESS'],
  ['Observatório de Qualidade →','Quality Observatory →'],
  ['Estado operacional do Observatório','Observatory operational state',['Estado operacional do Observatory']],
  ['Cobertura de texto completo','Full-text coverage'],
  ['Idade do contexto','Context age'],
  ['Não classificados','Unclassified'],
  ['Verificações','Checks'],
  ['Atualizar Observatório','Refresh Observatory',['Atualizar Observatory']],
  ['Voltar ao Radar ↺','Back to Radar ↺'],
  ['falha fechada','fail-closed'],
  ['triagem','screening'],
  ['certeza','certainty'],
  ['escore de qualidade da evidência','evidence-quality score'],
  ['status do provedor','provider status'],
  ['FLUXO CIENTÍFICO','SCIENTIFIC WORKFLOW'],
  ['Fluxo científico visual','Visual scientific workflow'],
  ['Do mapa à decisão humana, sem atalhos científicos','From map to human decision, without scientific shortcuts'],
  ['Estrutura do corpus','Corpus structure'],
  ['Inspeção de sinais','Signal inspection'],
  ['Decisão explícita','Explicit decision'],
  ['Recorte atual','Current slice'],
  ['Levar domínio para Inteligência →','Carry domain to Intelligence →',['Levar domínio para Intelligence →']],
  ['Panorama do domínio','Domain landscape',['Landscape do domínio']],
  ['Volume estrutural + cobertura de pacotes de resultados; não é força da evidência.','Structural volume + result-bundle coverage; it is not evidence strength.',['Volume estrutural + cobertura de result bundles; não é força da evidência.']],
  ['documentos mapeados','mapped documents'],
  ['pacote de resultados materializado','materialized result bundle',['result bundle materializado']],
  ['Domínio em inspeção','Domain under inspection'],
  ['Ver no mapa','View on map'],
  ['Abrir Revisão Humana →','Open Human Review →',['Abrir Human Review →']],
  ['Avaliação travada','Locked assessment'],
  ['Progresso desta avaliação','Assessment progress'],
  ['Itens de revisão concluídos','Completed review items'],
  ['Etapa humana isolada','Isolated human stage'],
  ['Voltar à Inteligência','Back to Intelligence',['Voltar à Intelligence']],
  ['Mapa e Inteligência organizam navegação e inspeção. Nenhum filtro, volume, recorrência ou clique cria elegibilidade, inclusão, certeza, EvidenceClaim, decisão de Revisão ou PRISMA.','Map and Intelligence organize navigation and inspection. No filter, volume, recurrence, or click creates eligibility, inclusion, certainty, an EvidenceClaim, a Review decision, or PRISMA.',['Mapa e Intelligence organizam navegação e inspeção. Nenhum filtro, volume, recorrência ou clique cria elegibilidade, inclusão, certeza, EvidenceClaim, decisão de Review ou PRISMA.']],
  ['ESPAÇO DE SÍNTESE DE PESQUISA','RESEARCH SYNTHESIS WORKSPACE'],
  ['Do julgamento humano à recuperação fundamentada — sem promoção automática','From human judgment to grounded retrieval — without automatic promotion',['Do julgamento humano ao retrieval grounded — sem promoção automática']],
  ['Recuperação fundamentada','Grounded retrieval'],
  ['Fluxo de síntese e recuperação','Synthesis and retrieval flow',['Fluxo de síntese e retrieval']],
  ['Revisão, Resumo e Pergunte são superfícies distintas. Navegar entre elas não cria síntese canônica, EvidenceClaim, elegibilidade, RoB, certeza, recomendação, PRESS, GF-10 ou PRISMA. Pergunte ao NutEV não importa automaticamente decisões da Revisão nem o Resumo.','Review, Brief, and Ask are distinct surfaces. Navigating between them does not create canonical synthesis, an EvidenceClaim, eligibility, RoB, certainty, recommendation, PRESS, GF-10, or PRISMA. Ask NutEV does not automatically import decisions from Review or the Brief.',['Review, Brief e Ask são superfícies distintas. Navegar entre elas não cria canonical synthesis, EvidenceClaim, elegibilidade, RoB, certainty, recomendação, PRESS, GF-10 ou PRISMA. Ask NutEV não importa automaticamente decisões do Review nem o Brief.']],
  ['Estado operacional da Revisão','Review operational state',['Estado operacional do Review']],
  ['rascunho local','local draft'],
  ['Revisor','Reviewer'],
  ['Comparações da âncora','Anchor comparisons'],
  ['Registro local','Local ledger',['Ledger local']],
  ['Exportar revisão','Export review'],
  ['Abrir Resumo →','Open Brief →',['Abrir Brief →']],
  ['Estado operacional do Resumo','Brief operational state',['Estado operacional do Brief']],
  ['Artefato humano compatível com o contexto atual.','Human artifact compatible with the current context.'],
  ['Importe uma Revisão exportada para executar a verificação com falha fechada.','Import an exported Review to run fail-closed verification.',['Importe um Review exportado para executar a verificação fail-closed.']],
  ['decisões humanas','Human decisions'],
  ['Semântica','Semantics'],
  ['verificado + não canônico','verified + noncanonical'],
  ['não canônico','noncanonical'],
  ['integridade verificada ≠ validado cientificamente','integrity verified ≠ scientifically validated'],
  ['← Voltar à Revisão','← Back to Review',['← Voltar ao Review']],
  ['Abrir Pergunte ao NutEV →','Open Ask NutEV →',['Abrir Ask NutEV →']],
  ['Estado operacional do Pergunte','Ask operational state',['Estado operacional do Ask']],
  ['Contexto','Context'],
  ['Recuperação','Retrieval'],
  ['Seleção','Selection'],
  ['disponível','available'],
  ['indisponível / carregando','unavailable / loading'],
  ['pacote de contexto materializado','context packet materialized'],
  ['pacote de contexto ainda não materializado','context packet not yet materialized'],
  ['← Ver Resumo','← View Brief',['← Ver Brief']],
  ['Gerar contexto fundamentado','Build grounded context',['Gerar contexto grounded']],
  ['EXPLORAÇÃO VISUAL','VISUAL EXPLORATION'],
  ['Leitura rápida do recorte','Quick slice overview'],
  ['Abrir recorte no Corpus ↗','Open slice in Corpus ↗'],
  ['Mix de texto completo','Full-text mix'],
  ['Status técnico do recorte','Technical status of the slice'],
  ['Mix de provedores','Provider mix'],
  ['Participação por fonte no recorte','Share by source in the slice'],
  ['Rotas de revisão','Review routes'],
  ['Rotas operacionais podem se sobrepor','Operational routes may overlap'],
  ['Pulso de publicações','Publication pulse'],
  ['Filtro cruzado','Cross-filter'],
  ['Recuperado','Retrieved'],
  ['Parcial','Partial'],
  ['Indisponível','Unavailable'],
  ['Não recuperado','Not retrieved'],
  ['Não tentado','Not attempted'],
  ['Desconhecido','Unknown'],
  ['Documentos','Documents'],
  ['Provedores','Providers'],
  ['Janela temporal','Time window'],
  ['fontes presentes','sources present'],
  ['sem ano disponível','no year available'],
  ['Sem documentos no recorte.','No documents in the slice.'],
  ['Sem provedores no recorte.','No providers in the slice.',['Sem providers no recorte.']],
  ['Ano de publicação indisponível neste recorte.','Publication year unavailable in this slice.'],
  ['em sobreposição','in overlap',['em overlap']],
  ['Painel científico avançado','Advanced scientific dashboard'],
  ['Apresentação v2','Presentation v2'],
  ['Visão de foco','Focus view'],
  ['PROJETO ATIVO · ARTIGO 1','ACTIVE PROJECT · ARTICLE 1'],
  ['Pipeline científico','Scientific pipeline'],
  ['Funil de processamento de evidências','Evidence processing funnel'],
  ['Prontidão da busca formal','Formal search readiness'],
  ['Método de extração','Extraction method'],
  ['Rotas do Artigo 1','Article 1 routes'],
  ['Tipos de documento','Document types'],
  ['Domínios operacionais','Operational domains'],
  ['Operações dos provedores','Provider operations'],
  ['Proveniência e contexto de IA','Provenance & AI context'],
  ['Registro de síntese','Synthesis Registry'],
  ['Liberação governada','Governed Release'],
  ['Manifesto de publicação','Publication Manifest'],
  ['Provedor','Provider'],
  ['Ordenação','Ranking'],
  ['Espaço de trabalho','Workspace'],
  ['Aplicação de pesquisa','Research Application'],
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
  ['Acesso autenticado aos espaços de trabalho e projetos do NutEV Motor de Evidências.','Authenticated access to NutEV Evidence Engine workspaces and projects.',['Acesso autenticado aos workspaces e projetos do NutEV Evidence Engine.']],
  ['Autenticação identifica a sessão. Permissões continuam sendo revalidadas no servidor para cada espaço de trabalho, projeto e operação privada.','Authentication identifies the session. Permissions continue to be revalidated by the backend for each workspace, project, and private operation.',['Autenticação identifica a sessão. Permissões continuam sendo revalidadas no backend para cada workspace, projeto e operação privada.']],
  ['Entre para acessar seus espaços de trabalho, pesquisas, biblioteca de evidências, aplicações metodológicas e exportações com isolamento de contexto.','Sign in to access your workspaces, research, evidence library, methodological applications, and exports with context isolation.',['Entre para acessar seus workspaces, pesquisas, biblioteca de evidências, aplicações metodológicas e exportações com isolamento de contexto.']],
  ['Fonte externa consultada pelo NutEV, como PubMed, Europe PMC, OpenAlex, Crossref, DOAJ, SciELO ou LILACS/BVS.','External source queried by NutEV, such as PubMed, Europe PMC, OpenAlex, Crossref, DOAJ, SciELO, or LILACS/BVS.'],
  ['Ordem de apresentação condicionada à consulta, combinando relevância para a busca e prioridade operacional NutEV. Não significa qualidade, certeza ou recomendação.','Query-conditioned presentation order combining search relevance and NutEV operational priority. It does not mean quality, certainty, or recommendation.'],
  ['Espaço de trabalho que reúne projetos e define a fronteira principal de acesso privado.','Workspace that groups projects and defines the main private-access boundary.'],
  ['Contexto de pesquisa dentro de um espaço de trabalho. Busca, biblioteca, revisão e exportação são autorizadas novamente para esse contexto.','Research context inside a workspace. Search, library, review, and export are authorized again for that context.',['Contexto de pesquisa dentro de um workspace. Busca, biblioteca, revisão e exportação são autorizadas novamente para esse contexto.']],
  ['Definições da interface para reduzir ambiguidade sem alterar os contratos científicos internos.','Interface definitions that reduce ambiguity without changing internal scientific contracts.'],
  ['Ex.: ordenação, espaço de trabalho, proveniência','E.g.: ranking, workspace, provenance',['Ex.: ranking, workspace, proveniência']],
  ['Nenhum documento mapeado pelo perfil atual','No documents mapped by the current profile'],
  ['Nenhum documento mapeado','No documents mapped'],
  ['lacuna de evidência','evidence gap'],
  ['texto completo','full text'],
  ['pacote de resultados','result bundle']
]

const EXACT=new Map()
for(const [pt,en,aliases=[]] of PAIRS){
  const entry={pt,en}
  EXACT.set(pt,entry)
  EXACT.set(en,entry)
  for(const alias of aliases)EXACT.set(alias,entry)
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
    pt:/^(\d+) domínios$/,
    en:/^(\d+) domains$/,
    toPt:match=>`${match[1]} domínios`,
    toEn:match=>`${match[1]} domains`
  },
  {
    pt:/^(\d+)\/([0-9]+) com pacote de resultados materializado$/,
    en:/^(\d+)\/([0-9]+) with materialized result bundle$/,
    aliases:[/^(\d+)\/([0-9]+) com result bundle materializado$/],
    toPt:match=>`${match[1]}/${match[2]} com pacote de resultados materializado`,
    toEn:match=>`${match[1]}/${match[2]} with materialized result bundle`
  },
  {
    pt:/^(\d+)\/([0-9]+) itens com decisão salva$/,
    en:/^(\d+)\/([0-9]+) items with a saved decision$/,
    toPt:match=>`${match[1]}/${match[2]} itens com decisão salva`,
    toEn:match=>`${match[1]}/${match[2]} items with a saved decision`
  },
  {
    pt:/^(\d+)\/([0-9]+) revisores enviaram e travaram a própria avaliação$/,
    en:/^(\d+)\/([0-9]+) reviewers submitted and locked their own assessment$/,
    toPt:match=>`${match[1]}/${match[2]} revisores enviaram e travaram a própria avaliação`,
    toEn:match=>`${match[1]}/${match[2]} reviewers submitted and locked their own assessment`
  },
  {
    pt:/^(\d+) recuperados \+ parciais$/,
    en:/^(\d+) retrieved \+ partial$/,
    toPt:match=>`${match[1]} recuperados + parciais`,
    toEn:match=>`${match[1]} retrieved + partial`
  }
]

const SKIP_SELECTOR='script,style,code,pre,textarea,[data-raw-enum],[data-i18n-skip],[data-nutev-no-translate],.article-title,[data-article-title],.abstract,[data-abstract],.source-title,[data-source-title],.finding-excerpt,[data-finding-excerpt],blockquote,cite'
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
    const matchAlias=(pattern.aliases||[]).map(alias=>core.match(alias)).find(Boolean)
    const match=matchPt||matchEn||matchAlias
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
  }else{
    switcher.classList.add('nutev-language-switch-floating')
    document.body.appendChild(switcher)
  }
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
