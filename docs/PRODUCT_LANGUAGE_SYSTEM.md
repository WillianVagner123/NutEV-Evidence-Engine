# NutEV — contrato de linguagem do produto

## Objetivo

O NutEV deve ser apresentado como um **Sistema de Evidências Científicas**, não como um chatbot, assistente, agente ou interface de modelo de linguagem.

A linguagem do produto descreve **funções científicas, operações, estados e limites verificáveis**. A tecnologia usada internamente não define o nome das superfícies do produto.

O idioma padrão é **Português (Brasil)**. A interface pode ser alternada para **English** sem mudar estado científico, permissões, dados, busca, revisão ou governança.

## Vocabulário canônico

| Conceito | Português | English | O que significa | Evitar na interface |
| --- | --- | --- | --- | --- |
| Produto | **Sistema de Evidências Científicas** | **Scientific Evidence System** | Plataforma para buscar, organizar, inspecionar, revisar e governar evidências com rastreabilidade. | Evidence Engine como subtítulo principal, AI system, LLM tool |
| Exploração documental | **Explorador de Evidências** | **Evidence Explorer** | Navegação documental e inspeção de metadados/contexto. | AI explorer |
| Estrutura do corpus | **Mapa de Evidências** | **Evidence Map** | Visualização estrutural do corpus verificado. | mapa de qualidade, mapa de certeza |
| Inspeção analítica | **Análise de Evidências** | **Evidence Analysis** | Organiza sinais, domínios, achados candidatos e filas de comparação. Não toma decisão científica. | Scientific Intelligence, AI intelligence |
| Etapa humana | **Revisão Humana** | **Human Review** | Registro explícito de julgamento humano. | automated review quando houver decisão humana |
| Revisão de síntese | **Revisão de Síntese** | **Synthesis Review** | Julgamento humano rastreável de comparabilidade e relação entre achados. | Human Synthesis Review como marca principal |
| Resumo verificado | **Resumo de Síntese Verificado** | **Verified Synthesis Summary** | Apresentação derivada de artefato humano cuja integridade/contexto foram verificados. | Brief como nome principal; “validado cientificamente” sem evidência correspondente |
| Consulta | **Consulta de Evidências** | **Evidence Query** | Consulta determinística do corpus verificado com documentos de suporte e correspondência explicável. | Ask NutEV, chat, assistant, prompt interface |
| Contexto do sistema | **Contexto de Evidências** | **Evidence Context** | Camada somente leitura com estado, manifesto e resumos estruturados usados pelas operações do sistema. | AI Context, agent context como rótulo visível |
| Exportação de consulta | **Pacote de Evidências** | **Evidence Packet** | Artefato auditável com pergunta, recorte, documentos de suporte, contexto verificado e regras de análise. | prompt packet, grounded prompt |
| Resultado estruturado | **Pacote de resultados** | **Result bundle** | Estrutura técnica materializada a partir de um documento. Não equivale a EvidenceClaim aceita. | finding-ready como rótulo de usuário |
| Disponibilidade para inspeção | **Pronto para inspeção** | **Ready for inspection** | Há material estruturado disponível para inspeção. | finding-ready na interface |
| Fonte externa | **Fonte** | **Source** | Serviço consultado pelo NutEV, como PubMed, Europe PMC, OpenAlex ou Crossref. | provider no modo PT |
| Ordenação | **Ordenação de busca** | **Search ranking** | Ordem operacional/relevância da consulta; não representa qualidade, certeza ou recomendação. | score de qualidade, ranking científico |
| Acesso privado | **Espaço de trabalho** | **Workspace** | Fronteira principal de acesso privado que reúne projetos. | workspace no modo PT |
| Pesquisa dentro do espaço | **Projeto** | **Project** | Contexto de trabalho científico autorizado dentro de um espaço de trabalho. | project misturado ao PT quando houver rótulo traduzível |
| Configuração metodológica | **Aplicação de pesquisa** | **Research Application** | Configuração explícita de método/uso vinculada ao projeto. | app genérico quando isso ocultar o significado científico |
| Segurança operacional | **Bloqueio por segurança** | **Fail-closed** | O sistema bloqueia a operação quando falta evidência/verificação necessária para prosseguir com segurança. | fail-closed sem explicação no modo PT |
| Texto do artigo | **Texto completo** | **Full text** | Conteúdo integral recuperado quando permitido/disponível. | full text no modo PT |
| Lacuna | **Lacuna de evidência** | **Evidence gap** | Conclusão que exige método apropriado; baixa contagem ou célula vazia não basta. | gap como inferência automática |
| Estado estrutural | **Sem uso de ranking científico** | **Rank-blind** | A organização não utiliza ranking para promover significado científico. | rank-blind isolado sem explicação no modo PT |

## Como explicar as superfícies

### Consulta de Evidências

A Consulta de Evidências **não é uma conversa com um modelo**. Ela executa correspondência determinística sobre o corpus verificado, apresenta documentos de suporte, explica sinais de correspondência e pode montar um Pacote de Evidências auditável.

**Limite:** correspondência lexical não significa relevância científica validada; consulta não significa inclusão; perfil automatizado não significa risco de viés ou certeza.

### Contexto de Evidências

O Contexto de Evidências é uma camada **somente leitura** que disponibiliza o estado verificado do projeto para operações e integrações do sistema.

**Limite:** contexto não é adjudicação científica, não cria inclusão e não autoriza PRESS, GF-10, congelamento de consulta, busca formal ou PRISMA.

### Análise de Evidências

A Análise de Evidências organiza domínio, classe documental, disponibilidade de pacotes de resultados, recorrências e filas de comparação para inspeção.

**Limite:** volume não significa força; recorrência não significa consenso; mapeamento esparso não significa lacuna de evidência; pacote de resultados não significa EvidenceClaim aceita.

### Revisão de Síntese

A Revisão de Síntese registra comparabilidade, relação e justificativa humanas em artefato rastreável.

**Limite:** relação humana não é meta-análise; convergência não significa certeza; divergência não prova contradição; rascunho não é síntese canônica.

### Resumo de Síntese Verificado

O Resumo verifica a integridade e compatibilidade contextual de um artefato de revisão humana e organiza sua apresentação.

**Limite:** SHA-256 detecta alteração de conteúdo, mas não prova autoria; integridade verificada não equivale a validação científica.

## Regras de redação

1. **Nomear a função, não a tecnologia.** Preferir “Consulta de Evidências” a “Ask”, “Contexto de Evidências” a “AI Context”.
2. **Não antropomorfizar.** Evitar “o NutEV pensa”, “o NutEV acredita”, “o NutEV conversa” ou “o NutEV decide” quando a operação é busca, filtragem, cálculo, classificação automatizada ou organização.
3. **Explicar o limite junto do resultado.** Contagem, correspondência, rota, disponibilidade de texto e perfil automatizado não devem parecer decisões científicas.
4. **Português limpo no modo PT.** Termos como provider, workspace, brief, finding-ready, retrieval, full text e fail-closed devem aparecer em português quando houver equivalente claro.
5. **Inglês coerente no modo EN.** A troca de idioma é de apresentação; não cria um segundo estado científico.
6. **Preservar nomes metodológicos reais.** PRESS, GF-10, PRISMA, B-NORM, C-STRUCT, SHA-256, DOI, PMID e EvidenceClaim permanecem quando forem identificadores/metodologias canônicas.
7. **Preservar conteúdo científico original.** Títulos, abstracts, citações, excertos e valores brutos da evidência não são traduzidos automaticamente.

## Exceção técnica interna

Alguns nomes históricos permanecem **internamente** para compatibilidade e auditoria, por exemplo:

- `AI_CONTEXT.md`;
- `/api/agent-context/...` e `/agent-context/...`;
- campos legados como `llm_context_chars`;
- verificações de segurança que citam OpenAI, Anthropic, ChatGPT, Claude, Gemini ou “LLM” para garantir que etapas científicas críticas não chamem serviços externos indevidos;
- identificadores/versionamentos já persistidos, como `NUTEV_SCIENTIFIC_INTELLIGENCE_VIEW_V1`.

Esses nomes são **contratos técnicos**, não branding de produto. Eles não devem ser usados como rótulos principais, chamadas de ação, títulos de página ou explicações ao usuário.

## Regra de governança

Mudança de nomenclatura **não altera estado científico**. Termos mais claros não transformam perfil automatizado em avaliação humana, pacote de resultados em EvidenceClaim, integridade em validade científica, nem navegação em PRISMA.
