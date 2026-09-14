const STORAGE_KEY='nutev_language'
const DEFAULT_LANGUAGE='pt-BR'
const ENGLISH_LANGUAGE='en'

// Product language is function-first. Legacy/mixed labels stay only as aliases so
// existing pages can be normalized without exposing AI/LLM branding to users.
const PAIRS=[
  ['Sistema de Evidências Científicas','Scientific Evidence System',['Evidence Engine','Motor de Evidências']],
  ['Idioma','Language'],
  ['Português','Portuguese'],
  ['Inglês','English'],
  ['Navegação principal','Primary navigation'],
  ['Abrir navegação','Open navigation'],
  ['Fechar navegação','Close navigation'],
  ['Pular para o conteúdo principal','Skip to main content'],
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
  ['Análise de Evidências','Evidence Analysis',['Scientific Intelligence','Inteligência Científica']],
  ['Revisão Humana','Human Review'],
  ['Revisão de Síntese','Synthesis Review',['Human Synthesis Review','Revisão Humana de Síntese']],
  ['Resumo de Síntese','Synthesis Summary',['Synthesis Brief']],
  ['Resumo de Síntese Verificado','Verified Synthesis Summary',['Verified Synthesis Brief']],
  ['Consulta de Evidências','Evidence Query',['Ask NutEV','Pergunte ao NutEV']],
  ['Contexto de Evidências','Evidence Context',['AI Context','Contexto de IA']],
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
  ['Revisão humana','Human review'],
  ['Resumo executivo','Executive summary',['Executive brief']],
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
  ['Síntese por domínio','Domain synthesis'],
  ['Candidatos a achados vinculados à fonte','Source-linked finding candidates'],
  ['Rótulos de desfecho recorrentes','Recurring outcome labels'],
  ['Fila de revisão de convergência / divergência','Convergence / divergence review queue'],
  ['Sinais de cobertura do corpus','Corpus coverage signals'],
  ['Nenhum domínio selecionado.','No domain selected.'],
  ['Abrir revisão humana →','Open human review →'],
  ['INTERPRETAÇÃO CIENTÍFICA · SOMENTE NAVEGAÇÃO','SCIENTIFIC INTERPRETATION · NAVIGATION ONLY'],
  ['Estruturar','Structure'],
  ['Inspecionar','Inspect'],
  ['Estruturar → Inspecionar → Revisão humana','Structure → Inspect → Human review'],
  ['Navegador de concentração por domínio','Domain concentration navigator'],
  ['volume ≠ força','volume ≠ strength'],
  ['Panorama de inspeção por domínio','Domain inspection overview',['Domain inspection panorama']],
  ['materializado ≠ alegação aceita','materialized ≠ accepted claim',['finding-ready ≠ accepted claim']],
  ['corpus mapeado','mapped corpus'],
  ['pronto para inspeção no domínio','ready for inspection within domain',['finding-ready within domain']],
  ['Progresso de envio humano','Human submission progress'],
  ['envio ≠ resultado científico','submission ≠ scientific outcome'],
  ['Minha avaliação aberta','My open assessment'],
  ['CICLO OPERACIONAL DE PESQUISA','OPERATIONAL RESEARCH CYCLE'],
  ['Observar','Observe'],
  ['Preparar','Prepare'],
  ['Verificar','Verify'],
  ['somente navegação','navigation only'],
  ['Ciclo operacional de pesquisa','Operational research cycle'],
  ['Estado operacional do Radar','Radar operational state'],
  ['Tópicos com lacunas','Topics with gaps',['Tópicos com gaps']],
  ['Busca ativa requerida','Active search required'],
  ['Fontes observadas','Observed sources',['Provedores observados','Observed providers']],
  ['Lacunas técnicas','Technical gaps',['Gaps técnicos']],
  ['Busca ativa','Active search'],
  ['Fontes / Monitoramento','Sources / Monitoring',['Providers / Watch','Provedores / Monitoramento']],
  ['Atualizar Radar','Refresh Radar'],
  ['Ver monitoramento','View monitoring',['Ver Watch']],
  ['Abrir Laboratório de Estratégia →','Open Strategy Lab →',['Abrir Strategy Lab →']],
  ['Estado operacional da Estratégia','Strategy operational state',['Estado operacional da Strategy']],
  ['rascunho','draft'],
  ['Congelamento da consulta','Query freeze'],
  ['Busca formal','Formal search'],
  ['Testes delta','Delta tests'],
  ['Abrir controle de qualidade','Open quality control',['Abrir QA','Open QA']],
  ['Abrir PRESS','Open PRESS'],
  ['Observatório de Qualidade →','Quality Observatory →'],
  ['Estado operacional do Observatório','Observatory operational state',['Estado operacional do Observatory']],
  ['Cobertura de texto completo','Full-text coverage'],
  ['Idade do contexto','Context age'],
  ['Não classificados','Unclassified'],
  ['Verificações','Checks'],
  ['Atualizar Observatório','Refresh Observatory',['Atualizar Observatory']],
  ['Voltar ao Radar ↺','Back to Radar ↺'],
  ['bloqueio por segurança','fail-closed',['falha fechada','fail-closed']],
  ['triagem','screening'],
  ['certeza','certainty'],
  ['escore de qualidade da evidência','evidence-quality score'],
  ['estado da fonte','source status',['status do provedor','provider status']],
  ['FLUXO CIENTÍFICO','SCIENTIFIC WORKFLOW'],
  ['Fluxo científico visual','Visual scientific workflow'],
  ['Do mapa à decisão humana, sem atalhos científicos','From map to human decision, without scientific shortcuts'],
  ['Estrutura do corpus','Corpus structure'],
  ['Inspeção de sinais','Signal inspection'],
  ['Decisão explícita','Explicit decision'],
  ['Recorte atual','Current slice'],
  ['Levar domínio para Análise →','Carry domain to Analysis →',['Levar domínio para Inteligência →','Carry domain to Intelligence →','Levar domínio para Intelligence →']],
  ['Panorama do domínio','Domain overview',['Domain landscape','Landscape do domínio']],
  ['documentos mapeados','mapped documents'],
  ['pacote de resultados materializado','materialized result bundle',['result bundle materializado']],
  ['Domínio em inspeção','Domain under inspection'],
  ['Ver no mapa','View on map'],
  ['Abrir Revisão Humana →','Open Human Review →',['Abrir Human Review →']],
  ['Avaliação travada','Locked assessment'],
  ['Progresso desta avaliação','Assessment progress'],
  ['Itens de revisão concluídos','Completed review items'],
  ['Etapa humana isolada','Isolated human stage'],
  ['Voltar à Análise','Back to Analysis',['Voltar à Inteligência','Back to Intelligence','Voltar à Intelligence']],
  ['ESPAÇO DE SÍNTESE DE PESQUISA','RESEARCH SYNTHESIS AREA',['RESEARCH SYNTHESIS WORKSPACE']],
  ['Da revisão humana à consulta vinculada às fontes — sem promoção automática','From human review to source-linked evidence query — without automatic promotion',['Do julgamento humano à recuperação fundamentada — sem promoção automática','From human judgment to grounded retrieval — without automatic promotion','Do julgamento humano ao retrieval grounded — sem promoção automática']],
  ['Consulta vinculada às fontes','Source-linked evidence query',['Recuperação fundamentada','Grounded retrieval','retrieval grounded']],
  ['Fluxo de síntese e consulta','Synthesis and query flow',['Fluxo de síntese e recuperação','Synthesis and retrieval flow','Fluxo de síntese e retrieval']],
  ['Estado operacional da Revisão','Review operational state',['Estado operacional do Review']],
  ['rascunho local','local draft'],
  ['Revisor','Reviewer'],
  ['Comparações da âncora','Anchor comparisons'],
  ['Registro local','Local record',['Local ledger','Ledger local']],
  ['Exportar revisão','Export review'],
  ['Abrir Resumo →','Open Summary →',['Open Brief →','Abrir Brief →']],
  ['Estado operacional do Resumo','Summary operational state',['Brief operational state','Estado operacional do Brief']],
  ['Artefato humano compatível com o contexto atual.','Human artifact compatible with the current context.'],
  ['Importe uma Revisão exportada para executar a verificação com bloqueio por segurança.','Import an exported Review to run fail-closed verification.',['Importe uma Revisão exportada para executar a verificação com falha fechada.','Importe um Review exportado para executar a verificação fail-closed.']],
  ['decisões humanas','Human decisions'],
  ['Semântica','Semantics'],
  ['verificado + não canônico','verified + noncanonical'],
  ['não canônico','noncanonical'],
  ['integridade verificada ≠ validado cientificamente','integrity verified ≠ scientifically validated'],
  ['← Voltar à Revisão','← Back to Review',['← Voltar ao Review']],
  ['Abrir Consulta de Evidências →','Open Evidence Query →',['Abrir Pergunte ao NutEV →','Open Ask NutEV →','Abrir Ask NutEV →']],
  ['Estado operacional da Consulta','Query operational state',['Estado operacional do Pergunte','Ask operational state','Estado operacional do Ask']],
  ['Contexto','Context'],
  ['Recuperação','Retrieval'],
  ['Seleção','Selection'],
  ['disponível','available'],
  ['indisponível / carregando','unavailable / loading'],
  ['pacote de evidências materializado','evidence packet materialized',['pacote de contexto materializado','context packet materialized']],
  ['pacote de evidências ainda não materializado','evidence packet not yet materialized',['pacote de contexto ainda não materializado','context packet not yet materialized']],
  ['← Ver Resumo','← View Summary',['← View Brief','← Ver Brief']],
  ['Gerar pacote de evidências','Build evidence packet',['Gerar contexto fundamentado','Build grounded context','Gerar contexto grounded']],
  ['EXPLORAÇÃO VISUAL','VISUAL EXPLORATION'],
  ['Leitura rápida do recorte','Quick slice overview'],
  ['Abrir recorte no Corpus ↗','Open slice in Corpus ↗'],
  ['Distribuição de texto completo','Full-text distribution',['Mix de texto completo','Full-text mix']],
  ['Estado técnico do recorte','Technical status of the slice',['Status técnico do recorte']],
  ['Distribuição por fonte','Source distribution',['Mix de provedores','Provider mix']],
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
  ['Fontes','Sources',['Provedores','Providers']],
  ['Fonte','Source',['Provedor','Provider']],
  ['Janela temporal','Time window'],
  ['fontes presentes','sources present'],
  ['sem ano disponível','no year available'],
  ['Sem documentos no recorte.','No documents in the slice.'],
  ['Sem fontes no recorte.','No sources in the slice.',['Sem provedores no recorte.','No providers in the slice.']],
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
  ['Operações das fontes','Source operations',['Operações dos provedores','Provider operations']],
  ['Proveniência e contexto de evidências','Provenance & evidence context',['Proveniência e contexto de IA','Provenance & AI context']],
  ['Registro de síntese','Synthesis Registry'],
  ['Liberação governada','Governed Release'],
  ['Manifesto de publicação','Publication Manifest'],
  ['Ordenação de busca','Search ranking',['Ordenação','Ranking']],
  ['Espaço de trabalho','Workspace',['workspace']],
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
  ['pacote de resultados','result bundle',['result bundles']],
  ['síntese canônica','canonical synthesis'],
  ['sem uso de ranking científico','rank-blind',['rank-blind']],
  ['perfil automatizado','automated profile',['machine profile']],
  ['texto completo recuperado','retrieved full text'],
  ['Regras de análise','Analysis rules',['Prompt canônico para agentes','INSTRUCTIONS FOR THE ANALYZING AGENT']],
  ['Instruções de análise','Analysis instructions',['prompt auditável','Copiar prompt','Canonical prompt']],
  ['Pacote de evidências','Evidence packet',['Grounded context packet','context packet']],
  ['Documentos de suporte','Supporting documents'],
  ['consulta vinculada às fontes','source-linked query',['grounded retrieval']],
  ['Documentos primeiro. Síntese depois.','Documents first. Synthesis second.',['Evidence first. Generation second.']]
]

// Full-page product copy introduced by the system-first language pass.
// Keeping it separate makes the conceptual vocabulary above easier to audit.
const PRODUCT_COPY_PAIRS=[
  ['Análise de Evidências — NutEV','Evidence Analysis — NutEV',['Scientific Intelligence — NutEV']],
  ['Consulta de Evidências — NutEV','Evidence Query — NutEV',['Ask NutEV — Grounded Evidence Retrieval']],
  ['Contexto de Evidências — NutEV','Evidence Context — NutEV',['AI Context — NutEV']],
  ['Revisão de Síntese — NutEV','Synthesis Review — NutEV',['Human Synthesis Review — NutEV']],
  ['Resumo de Síntese Verificado — NutEV','Verified Synthesis Summary — NutEV',['Human Synthesis Brief — NutEV']],
  ['Controle de qualidade','Quality control',['QA']],
  ['Pergunta','Question'],
  ['Limpar','Clear'],
  ['Todos os domínios','All domains'],
  ['Todos os tipos','All document types'],
  ['carregando contexto…','loading context…'],
  ['Faça uma pergunta para iniciar.','Enter a question to begin.'],
  ['0 selecionados','0 selected'],
  ['Nenhuma consulta executada.','No query executed.'],
  ['Gerar pacote','Build packet'],
  ['Copiar pacote','Copy packet'],
  ['Avaliação + monitoramento','Assessment + monitoring'],
  ['Contexto social','Social context'],
  ['Literacia alimentar','Food literacy'],
  ['Medicina do Estilo de Vida','Lifestyle Medicine'],
  ['Consulte o corpus estruturado e veja primeiro os documentos que sustentam cada resultado.','Query the structured corpus and see the supporting documents first.'],
  ['ARTIGO 1 · CONSULTA VINCULADA ÀS FONTES','ARTICLE 1 · SOURCE-LINKED EVIDENCE QUERY'],
  ['A consulta usa correspondência determinística sobre o corpus verificado do Artigo 1, explica por que cada documento apareceu e organiza um pacote auditável para análise. Nenhum resultado é promovido automaticamente a evidência científica aceita.','The query uses deterministic matching over the verified Article 1 corpus, explains why each document appeared and organizes an auditable packet for analysis. No result is automatically promoted to accepted scientific evidence.'],
  ['consulta determinística','deterministic query'],
  ['Quais documentos normativos tratam de avaliação nutricional e monitoramento?','Which normative documents address nutrition assessment and monitoring?'],
  ['Quais documentos abordam contexto social da alimentação?','Which documents address the social context of eating?'],
  ['Quais diretrizes e estruturas abordam literacia alimentar ou competências alimentares?','Which guidelines and frameworks address food literacy or food skills?'],
  ['Compare documentos B-NORM e C-STRUCT relacionados à Medicina do Estilo de Vida.','Compare B-NORM and C-STRUCT documents related to Lifestyle Medicine.'],
  ['Carregando os resumos científicos verificados…','Loading verified scientific summaries…'],
  ['Use documentos selecionados; se nenhum estiver marcado, o sistema usa os melhores resultados da consulta.','Use selected documents; if none are checked, the system uses the best query matches.'],
  ['O pacote de evidências aparecerá aqui.','The evidence packet will appear here.'],
  ['O pacote contém metadados e contexto seguro, não texto completo protegido. Para aprofundar um documento, abra o Dossiê Científico no Corpus.','The packet contains metadata and safe context, not protected full text. To inspect a document more deeply, open its Scientific Dossier in the Corpus.'],
  ['Consulta ≠ inclusão. Correspondência lexical ≠ relevância científica validada. Pertencer a uma rota ≠ elegibilidade. Perfil automatizado ≠ risco de viés ou certeza. Excertos continuam candidatos até revisão humana. A Consulta de Evidências não autoriza PRESS, GF-10, congelamento da consulta, busca formal ou PRISMA.','Query ≠ inclusion. Lexical match ≠ validated scientific relevance. Route membership ≠ eligibility. Automated profile ≠ risk of bias or certainty. Excerpts remain candidates until human review. Evidence Query does not authorize PRESS, GF-10, query freeze, formal search or PRISMA.'],
  ['Fonte compartilhada e auditável para as operações e integrações do sistema.','Shared and auditable source for system operations and integrations.'],
  ['CONTEXTO AUDITÁVEL · ARTIGO 1','AUDITABLE CONTEXT · ARTICLE 1'],
  ['Uma fonte de verdade para o sistema','A single source of truth for the system'],
  ['Busca, análise e integrações devem usar o mesmo estado de busca, manifesto e resumos estruturados. O sistema não reconstrói estado científico a partir de histórico de conversa nem cria fatos ausentes.','Search, analysis and integrations must use the same search state, manifest and structured summaries. The system does not reconstruct scientific state from conversation history or create missing facts.'],
  ['Carregando contexto verificado…','Loading verified context…'],
  ['Arquivos canônicos','Canonical files'],
  ['Arquivos seguros disponibilizados ao sistema, sem texto completo protegido.','Safe files made available to the system, without protected full text.'],
  ['Abrir Consulta de Evidências →','Open Evidence Query →'],
  ['Limite da busca formal','Formal-search boundary'],
  ['O contexto reflete o estado mestre; não altera nem contorna gates científicos.','The context reflects the master state; it does not alter or bypass scientific gates.'],
  ['Instruções operacionais para consumir o contexto sem ultrapassar a fronteira científica.','Operational instructions for using the context without crossing the scientific boundary.'],
  ['Copiar instruções','Copy instructions'],
  ['Contexto de evidências ≠ adjudicação. Perfil automatizado ≠ inclusão. Pertencer a uma rota ≠ elegibilidade. Excerto ≠ EvidenceClaim aceito. A busca formal continua dependente de PRESS + GF-10 + congelamento da consulta.','Evidence context ≠ adjudication. Automated profile ≠ inclusion. Route membership ≠ eligibility. Excerpt ≠ accepted EvidenceClaim. Formal search remains dependent on PRESS + GF-10 + query freeze.'],
  ['Síntese por domínio · achados candidatos · filas de comparação humana','Domain synthesis · finding candidates · human comparison queues'],
  ['SUPORTE À SÍNTESE · SEM CONCLUSÃO AUTOMÁTICA','SYNTHESIS SUPPORT · NO AUTOMATED CONCLUSION'],
  ['Construindo síntese estrutural sem uso de ranking científico…','Building rank-blind structural synthesis…'],
  ['Achados candidatos vinculados às fontes','Source-linked finding candidates'],
  ['Selecione um domínio. O NutEV carrega somente um lote limitado de dossiês, sem texto completo integral.','Select a domain. NutEV loads only a limited batch of dossiers, without complete full text.'],
  ['O sistema prepara documentos comparáveis; não classifica automaticamente concordância, contradição ou certeza.','The system prepares comparable documents; it does not automatically classify agreement, contradiction or certainty.'],
  ['Domínios menos representados ou com menos pacotes de resultados são sinais para inspeção — não lacunas de evidência confirmadas.','Less represented domains or domains with fewer result bundles are signals for inspection — not confirmed evidence gaps.'],
  ['Contagem por domínio ≠ força · rótulo recorrente ≠ consenso · redação diferente ≠ contradição · mapeamento esparso ≠ lacuna de evidência · pacote de resultados ≠ EvidenceClaim aceita · esta página ≠ PRISMA.','Domain count ≠ strength · recurring label ≠ consensus · different wording ≠ contradiction · sparse mapping ≠ evidence gap · result bundle ≠ accepted EvidenceClaim · this page ≠ PRISMA.'],
  ['Comparabilidade · convergência/divergência · justificativa do revisor','Comparability · convergence/divergence · reviewer rationale'],
  ['Abrir Resumo','Open Summary'],
  ['Limpar rascunho','Clear draft'],
  ['JULGAMENTO HUMANO · RASCUNHO LOCAL · NÃO CANÔNICO','HUMAN JUDGMENT · LOCAL DRAFT · NONCANONICAL'],
  ['Transformar comparação visual em julgamento rastreável','Turn visual comparison into traceable judgment'],
  ['Preparando fila humana de síntese…','Preparing human synthesis queue…'],
  ['Achado âncora','Anchor finding'],
  ['Fila de adjudicação','Adjudication queue'],
  ['Registro da revisão','Review record'],
  ['Limite de interpretação','Interpretation boundary'],
  ['Referência fixa para a rodada de comparação atual.','Fixed reference for the current comparison round.'],
  ['Classifique comparabilidade antes de registrar convergência/divergência. Relação sem justificativa não é salva.','Classify comparability before recording convergence/divergence. A relation without rationale is not saved.'],
  ['Decisões humanas salvas localmente neste navegador. O registro é rascunho, fica vinculado à impressão digital do contexto atual e precisa ser exportado para circular como artefato.','Human decisions saved locally in this browser. The record is a draft, remains bound to the current context fingerprint and must be exported to circulate as an artifact.'],
  ['Rótulo de relação humana ≠ meta-análise · convergente ≠ certeza · divergente ≠ contradição comprovada · não comparável ≠ exclusão · rascunho ≠ síntese canônica · impressão digital do contexto ≠ validação científica · esta página ≠ PRISMA.','Human relation label ≠ meta-analysis · convergent ≠ certainty · divergent ≠ proven contradiction · not comparable ≠ exclusion · draft ≠ canonical synthesis · context fingerprint ≠ scientific validation · this page ≠ PRISMA.'],
  ['Artefato de revisão com integridade verificada · visão executiva para apresentação','Integrity-verified review artifact · executive presentation view'],
  ['Importar revisão','Import review'],
  ['Exportar resumo','Export summary'],
  ['aguardando revisão','waiting for review'],
  ['INTEGRIDADE VERIFICADA · FONTE HUMANA · NÃO REPRESENTA CERTEZA','INTEGRITY VERIFIED · HUMAN SOURCE · NOT CERTAINTY'],
  ['Visão executiva para artigo e apresentação científica','Executive view for article and scientific presentation'],
  ['Verificação do artefato de revisão','Review artifact verification'],
  ['Panorama das relações revisadas','Reviewed relationship landscape'],
  ['Domínios representados','Domains represented'],
  ['Perfil de comparabilidade','Comparability profile'],
  ['Relações revisadas','Reviewed relationships'],
  ['Limite de apresentação','Presentation boundary'],
  ['Desfecho','Outcome'],
  ['Construto / intervenção','Construct / intervention',['Construct / intervenção']],
  ['Tempo / seguimento','Time / follow-up',['Tempo / follow-up']],
  ['Não revisado','Unreviewed',['UNREVIEWED']],
  ['Nenhum domínio pronto para inspeção','No domain ready for inspection',['Nenhum domínio finding-ready']],
  ['pacote de resultados vinculado à fonte','source-linked result bundle'],
  ['Literacia alimentar / nutricional','Food / nutrition literacy'],
  ['Processo de Cuidado em Nutrição','Nutrition Care Process'],
  ['Posicionamento','Position statement'],
  ['Estrutura / modelo','Framework / model'],
  ['Competências / currículo','Competencies / curriculum'],
  ['Orientação','Guidance']
]

const EXACT=new Map()
for(const [pt,en,aliases=[]] of PAIRS){
  const entry={pt,en}
  EXACT.set(pt,entry)
  EXACT.set(en,entry)
  for(const alias of aliases)EXACT.set(alias,entry)
}
for(const [pt,en,aliases=[]] of PRODUCT_COPY_PAIRS){
  const entry={pt,en}
  EXACT.set(pt,entry)
  EXACT.set(en,entry)
  for(const alias of aliases)EXACT.set(alias,entry)
}

const DYNAMIC_PATTERNS=[
  {pt:/^(\d+) mapeamentos$/,en:/^(\d+) mapped placements$/,toPt:m=>`${m[1]} mapeamentos`,toEn:m=>`${m[1]} mapped placements`},
  {pt:/^Rodada (\d+)$/,en:/^Round (\d+)$/,toPt:m=>`Rodada ${m[1]}`,toEn:m=>`Round ${m[1]}`},
  {pt:/^(\d+) domínios$/,en:/^(\d+) domains$/,toPt:m=>`${m[1]} domínios`,toEn:m=>`${m[1]} domains`},
  {pt:/^(\d+)\/([0-9]+) com pacote de resultados materializado$/,en:/^(\d+)\/([0-9]+) with materialized result bundle$/,aliases:[/^(\d+)\/([0-9]+) com result bundle materializado$/],toPt:m=>`${m[1]}/${m[2]} com pacote de resultados materializado`,toEn:m=>`${m[1]}/${m[2]} with materialized result bundle`},
  {pt:/^(\d+)\/([0-9]+) itens com decisão salva$/,en:/^(\d+)\/([0-9]+) items with a saved decision$/,toPt:m=>`${m[1]}/${m[2]} itens com decisão salva`,toEn:m=>`${m[1]}/${m[2]} items with a saved decision`},
  {pt:/^(\d+)\/([0-9]+) revisores enviaram e travaram a própria avaliação$/,en:/^(\d+)\/([0-9]+) reviewers submitted and locked their own assessment$/,toPt:m=>`${m[1]}/${m[2]} revisores enviaram e travaram a própria avaliação`,toEn:m=>`${m[1]}/${m[2]} reviewers submitted and locked their own assessment`},
  {pt:/^(\d+) recuperados \+ parciais$/,en:/^(\d+) retrieved \+ partial$/,toPt:m=>`${m[1]} recuperados + parciais`,toEn:m=>`${m[1]} retrieved + partial`},
  {pt:/^contexto estruturado ([\d.,]+) caracteres$/,en:/^structured context ([\d.,]+) characters$/,aliases:[/^contexto IA ([\d.,]+) chars$/i],toPt:m=>`contexto estruturado ${m[1]} caracteres`,toEn:m=>`structured context ${m[1]} characters`},
  {pt:/^(.+) · pacote de resultados vinculado à fonte$/,en:/^(.+) · source-linked result bundle$/,toPt:m=>`${m[1]} · pacote de resultados vinculado à fonte`,toEn:m=>`${m[1]} · source-linked result bundle`}
]

const SKIP_SELECTOR='script,style,code,pre,textarea,[data-raw-enum],[data-i18n-skip],[data-nutev-no-translate],.article-title,[data-article-title],.abstract,[data-abstract],.source-title,[data-source-title],.finding-excerpt,[data-finding-excerpt],blockquote,cite'
const ATTRIBUTES=['placeholder','title','aria-label','aria-description','data-question']
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
    const match=core.match(pattern.pt)||core.match(pattern.en)||(pattern.aliases||[]).map(alias=>core.match(alias)).find(Boolean)
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

function t(pt,en){return currentLanguage===ENGLISH_LANGUAGE?en:pt}

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
