# Changelog

Mudanças públicas relevantes do NutEV Reference Engine são registradas aqui. O histórico completo de implementação permanece disponível no Git.

## [Unreleased]

### Integridade de entrega do deploy de produção

- **Corrigido um modo de falha em que um deploy parcialmente executado era reportado como sucesso.** A metade remota do deploy era um heredoc transmitido para `bash -s` pelo canal SSH; quando o canal era perturbado pela reinicialização do contêiner, o `bash` encontrava EOF no meio do script e saía com 0. O `ssh` retornava sucesso e o job ficava verde tendo pulado o contrato de runtime em produção, a asserção `/api/version == TARGET_SHA`, o smoke público HTTPS e o caminho de rollback. Um deploy real fez exatamente isso: o log não contém saída alguma dessas verificações.
- A metade remota passa a viver em `deploy/hetzner/remote_deploy.sh`, versionada e verificável. O workflow copia o arquivo para o host, confere o SHA-256 lá e só então o executa a partir do disco; uma conexão perdida durante a execução faz o `ssh` sair diferente de zero em vez de zero.
- O script imprime `NUTEV_REMOTE_DEPLOY_COMPLETE <sha>` como último ato e o workflow **falha o deploy quando essa linha está ausente**, por mais limpa que tenha sido a saída do `ssh`. Execução parcial não volta a passar por sucesso.
- Nenhuma lógica de deploy mudou: a extração é literal, e todo gate, ordenação e caminho de rollback permanece idêntico.

### Evidência de deploy

- Cada promoção grava seus JSON de verificação em um diretório com escopo de execução no host; o workflow busca esse diretório e o publica como artefato `hetzner-deploy-evidence-<run_id>-<attempt>`, junto com o log da sessão.
- A coleta roda com `if: always()` e nunca reprova o job, então um deploy revertido preserva a evidência que explica o motivo. Ler o artefato não exige acesso ao host.
- Adicionados testes de contrato para a integridade de entrega, incluindo verificação de que cada guarda falha quando a proteção correspondente é removida.
- Testes de contrato do deploy passam a ler a superfície combinada (workflow + script remoto) por meio de `nutev_tests/deploy_surface.py`, de modo que continuam enxergando a lógica que existem para proteger.


### Binding técnico do Artigo 1 / D-132

- Corrigido `tools/provision_doctorate_article1.py` para garantir, com `--article1-assembly`, tanto `assembly_id=WILLIAN_DOCTORATE_A1` quanto a `d132_config_version` lida da configuração canônica do D-132.
- O comando agora repara aplicação existente quando essas chaves estão ausentes, preservando a configuração privada já armazenada; valores conflitantes falham fechado em vez de serem sobrescritos.
- O reparo continua sendo somente configuração de acesso/aplicação: não altera PRESS, GF-10, query freeze, busca formal, PRISMA, D-132 humano nem ownership histórico.


### Primeiro login com workspace provisionado

- Corrigida a home do runtime multiusuário para distinguir conta sem workspace, conta com múltiplos workspaces e conta com exatamente um workspace ainda não selecionado. Nesse último caso, o contexto é selecionado pelo endpoint server-side antes de listar projetos, evitando a falsa mensagem "Nenhum projeto disponível" no primeiro acesso.


### Gestão de membros como superfície de produto

- Adicionados `GET /api/workspace/members`, `POST /api/workspace/members` e `POST /api/workspace/members/status`, expondo as primitivas de membership que antes só existiam para operador em terminal. Os três exigem `MEMBERS_MANAGE` (`WORKSPACE_OWNER` / `WORKSPACE_ADMIN`).
- O workspace alvo vem do contexto autenticado no servidor; `workspace_id` no corpo da requisição nunca é lido, então conhecer um identificador estrangeiro não alcança outro tenant.
- Conceder acesso exige conta já ativa: a superfície não cria identidade, não define senha e não concede papel global. Quem não concluiu o convite governado é recusado.
- Corrigida uma falha de propriedade encontrada na auditoria das primitivas: `add_or_update_member` recusava **atribuir** `WORKSPACE_OWNER`, mas não recusava **rebaixar** o proprietário vigente, permitindo que um `WORKSPACE_ADMIN` deixasse o workspace com um `owner_user_id` cujo membership não carregava mais autoridade de proprietário. As duas direções passam a ser recusadas.
- Alterar o papel de um membership existente exige confirmação explícita, em paralelo ao `--allow-role-change` da CLI de operador.
- Adicionada a tela `members.html`, acessível a partir da tela do projeto apenas quando o papel carrega `MEMBERS_MANAGE`. O formulário declara `method="post"` e `action` explícita, para que falha de JavaScript não vire submit GET com o e-mail na URL, no histórico e no `Referer`.
- Adicionado `list_memberships` ao store de tenancy, `list_members` ao `WorkspaceProjectService`, `find_active_subject_by_email` ao provedor de identidade e a constante canônica `ASSIGNABLE_WORKSPACE_ROLES`, da qual `WORKSPACE_OWNER` está deliberadamente ausente.

### Materialização do workspace do doutorado

- Adicionado `tools/provision_doctorate_article1.py`, comando de operador idempotente que cria o workspace, o projeto do Artigo 1 e a `ResearchApplication` de `SCOPING_REVIEW` para uma identidade que já existe, em vez de exigir Python escrito à mão contra o banco de produção.
- O comando nunca cria usuário, senha, papel global ou membership de terceiros, e nunca sobrescreve a configuração privada de um projeto já existente; re-executar devolve `already_provisioned` sem alterar nada.
- A marcação `assembly_id` do Artigo 1 é opt-in (`--article1-assembly`) e é configuração, não propriedade: os pins server-managed `NUTEV_A1_WORKSPACE_ID` / `NUTEV_A1_PROJECT_ID` continuam obrigatórios e continuam sendo um passo humano separado, apenas reportado pelo recibo.
- Recusa fail-closed com código de saída distinto para banco ausente, responsável inexistente ou inativo, e workspace cujo slug já pertence a outra identidade.

### Estado científico do Artigo 1 na interface

- Adicionado `GET /api/article1/scientific-state`, leitura que deriva Discovery, PRESS, GF-10, congelamento de consulta, busca formal e PRISMA da fonte canônica `config/nutev/article1_search_master_v1.json`.
- Valores não reconhecidos derivam estado **fechado**: um master malformado ou futuro nunca é lido como portão aberto. O endpoint não abre portão algum.
- A leitura exige `APPLICATION_READ` no projeto e o pin server-managed do Artigo 1; um projeto que não seja o Artigo 1 pinado recebe semântica de não encontrado, então o estado do A1 não vaza para a visão de outro tenant.
- A tela do projeto passa a exibir esse estado, com as contagens do corpus rotuladas como descoberta e recuperação — não como PRISMA, triagem, inclusão ou exclusão. O vínculo histórico é apresentado como vínculo de acesso, que não adota decisão científica alguma para o projeto.

### Interface consciente de papel

- A tela do projeto e a navegação lateral passam a ser derivadas do papel resolvido pelo servidor. Um orientador não recebe mais "Buscar evidências", "Laboratório avançado", o seletor de template ou a gestão de membros para descobrir a proibição só no 403.
- A interface não substitui autorização: o servidor continua reautorizando cada requisição, e a regressão de navegador chama os endpoints proibidos com a sessão real do orientador para provar a recusa.

### Testes e documentação do fluxo do doutorado

- Adicionada regressão de navegador com dois atores (`tools/run_doctorate_supervisor_browser.py`): responsável e orientador, incluindo recusas diretas de endpoint, provas cross-tenant com identificadores estrangeiros reais e verificação de que nenhum portão do Artigo 1 é renderizado como aberto. Integrada ao workflow `pilot-closeout`.
- Adicionado `tools/doctorate_supervisor_fixture.py`, fixture offline e descartável que cria apenas estado de tenancy e navegação — nenhum registro científico, busca, PRISMA, PRESS ou GF-10.
- Adicionados testes da superfície de membership: recusa de rebaixamento do proprietário, exigência de confirmação para troca de papel, negações do orientador nos endpoints reais, death tests cross-tenant e a cadeia completa solicitação -> aprovação -> senha -> login -> concessão de `ACADEMIC_SUPERVISOR` pela API.
- Adicionado `docs/DOCTORATE_ARTICLE1_ONBOARDING.md`, guia humano do Artigo 1 para o responsável e para o orientador, incluindo explicitamente que ter acesso ao Artigo 1 não é aprovar PRESS, autorizar GF-10, congelar consultas, aprovar busca formal nem criar PRISMA.

### Papel de supervisão acadêmica

- Adicionado o papel de workspace `ACADEMIC_SUPERVISOR` (**Professor orientador**) à matriz canônica `ROLE_PERMISSIONS`, com acesso somente leitura ao projeto (`APPLICATION_READ`, `SEARCH_HISTORY_READ`, `EVIDENCE_LIBRARY_READ`, `FULL_TEXT_ACCESS_READ`, `PROJECT_BANK_READ`, `HUMAN_REVIEW_READ`) e leitura de auditoria (`PROJECT_AUDIT_READ`); `EXPORT` permanece policy-gated.
- O papel não recebe escrita, execução de busca, triagem, extração, adjudicação, gestão de revisão humana, gestão de membros, criação ou exclusão de projeto. Conceder supervisão não amplia o que o workspace pode fazer.
- `ACADEMIC_SUPERVISOR` entrou em `_PROJECT_WIDE_ROLES`, então a resolução de contexto continua exigindo `confirm_project_access` server-side e a fronteira entre workspaces permanece fail-closed.
- Adicionado o rótulo `Professor orientador` ao seletor de contexto da interface e a entrada correspondente no contrato de linguagem do produto.
- Documentada a matriz de papéis em `docs/MULTITENANT_WORKSPACE_PROJECT_ACCESS.md`, com `ROLE_PERMISSIONS` explicitado como fonte única de verdade.
- Registrado explicitamente que membership de supervisão é concessão de acesso e **não** é aprovação do orientador: não cria elegibilidade, qualidade metodológica, risco de viés, certeza, recomendação, PRISMA, PRESS, GF-10 nem congelamento de consulta.
- Testes adicionados para o conjunto exato de permissões do papel, o gate de policy no export, a exigência de confirmação de acesso ao projeto e o isolamento entre workspaces.

### Provisionamento do acesso do orientador

- Adicionado `tools/grant_workspace_membership.py`, concessão de membership de workspace somente para operador, idempotente e fail-closed, com seleção do workspace por `--workspace-id` ou `--workspace-slug`.
- A ferramenta nunca cria usuários, senhas, workspaces, projetos, papéis globais ou estado científico; `WORKSPACE_OWNER` não é atribuível e continua exigindo o fluxo explícito de transferência.
- Trocar o papel de um membership existente exige `--allow-role-change`; sem a flag a operação é recusada sem alterar nada, para que mudança de privilégio nunca ocorra em silêncio.
- `invited_by` permanece nulo em concessões por CLI: não há Principal autenticado convidando e a ferramenta não personifica um.
- Adicionado `docs/ACADEMIC_SUPERVISOR_ONBOARDING.md`, runbook do caminho governado completo (solicitação -> aprovação -> convite de uso único -> senha definida pelo próprio orientador -> membership -> login), com códigos de saída e procedimento de revogação.
- Adicionado teste de contrato ponta a ponta do onboarding: conta recém-criada não enxerga workspace algum antes do membership, a concessão é idempotente, o envelope resultante é somente leitura, suspensão revoga no login seguinte e o isolamento entre workspaces se mantém.

### Homologação provisória de acesso

- Adicionado `tools/seed_homologation_access.py`, que materializa um ambiente descartável de homologação (responsável, workspace, projeto e a conta do orientador já com `ACADEMIC_SUPERVISOR`) para validar o caminho de acesso sem tocar em identidade de produção.
- O seeder é fail-closed por construção: não tem banco padrão, exige `NUTEV_ENVIRONMENT` não-produtivo (variável ausente conta como produção), recusa o caminho canônico de produção e o valor de `NUTEV_AUTH_DB`, recusa symlink e recusa banco que já contenha identidades.
- Senhas são geradas com `secrets`, impressas uma única vez em stdout e persistidas apenas como hash Argon2.
- Documentado o procedimento em `docs/ACADEMIC_SUPERVISOR_ONBOARDING.md`, incluindo as guardas, os códigos de saída e o limite do que a homologação evidencia.
- Adicionado teste de jornada HTTP real contra servidor pilot vivo: login do orientador, seleção de contexto, projeto visível, `POST /api/search/jobs` negado com 403, e o mesmo endpoint aceito com 202 para um papel que detém `SEARCH_RUN` — provando que o 403 é o papel, não uma rota quebrada.

## [1.1.0] - 2026-09-12

### Scientific Workspace v2

- Adicionado `/quality.html` como **Quality Observatory** somente-leitura para saúde operacional, proveniência, retrieval, completude de metadados, mapeamento, providers e estado dos gates, sem representar esses sinais como qualidade metodológica da evidência.
- Corrigida a interpretação do gate PRESS no dashboard: `NOT_YET_RECORDED_AS_PASS` não pode mais ser aceito por correspondência de substring; somente o valor canônico exato `PASS` aprova a apresentação do gate.
- Adicionado `tools/audit_scientific_workspace_v2.py`, death test adversarial executável para detectar regressões de semântica científica, mutações indevidas, promoção prematura de C4, vazamento de ranking no snapshot, falsa semântica PRISMA e totais de produção hardcoded.
- O job de CI `audit guardrail contract` passou a executar explicitamente o death test, além do contrato fail-closed de ranking.
- Adicionados testes específicos para Quality Observatory e para a regressão do parser de PRESS.
- Adicionado `/intelligence.html` como **Scientific Intelligence / Synthesis Layer** rank-blind, com síntese estrutural por domínio, classes documentais, rotas, cobertura de result bundles e sinais de cobertura do corpus.
- A inspeção de achados usa carregamento lazy de até 24 dossiês por domínio, com concorrência limitada e sem enviar full text integral ou o corpus detalhado inteiro ao navegador.
- Recorrência de outcome é apresentada apenas como rótulo estruturado repetido no lote carregado; convergência/divergência permanece fila de comparação para revisão humana, sem classificação automática de agreement, contradiction ou certainty.
- Sinais de baixa representação são explicitamente tratados como `corpus coverage signals`, nunca como `evidence gap` automático.
- O Scientific Workspace death test agora também falha se a synthesis layer reintroduzir ranking, mutações, consenso por recorrência, evidence gap automático ou carregamento detalhado não limitado.
- Adicionado `/synthesis-review.html` como **Human Synthesis Review**, com adjudicação pairwise explícita de comparabilidade em população, construct/intervenção, outcome e timeframe, seguida de relação humana `CONVERGENT`, `DIVERGENT`, `COMPLEMENTARY`, `NOT_COMPARABLE` ou `UNCLEAR`.
- Julgamentos humanos exigem identificação do revisor e justificativa mínima antes de serem salvos; nenhuma relação é preselecionada ou inferida automaticamente pelo frontend.
- O estado da Human Synthesis Review é um rascunho `canonical:false` armazenado somente no navegador, sem POST científico ao servidor e sem mutar PRESS, GF-10, freeze, screening, RoB, certainty ou PRISMA.
- A Human Synthesis Review agora deriva `context_fingerprint` determinístico de `search_id`, `context_version`, pergunta, SHA-256 do Workbench, SHA-256 do manifest de rotas, versão de review profile e contagem de Article Summaries; o armazenamento local também é escopado por esse fingerprint para não reutilizar silenciosamente decisões após rebuild do contexto.
- A exportação `NUTEV_HUMAN_SYNTHESIS_REVIEW_DRAFT_V1` inclui `context_source`, `context_fingerprint`, snapshots source-linked dos achados, decisões humanas e SHA-256 determinístico do conteúdo científico, permanecendo explicitamente não canônica.
- O death test adversarial passou a bloquear adjudicação automática, revisão anônima/sem justificativa, POST/LLM externo, detalhes não limitados, ausência de context fingerprint e qualquer export que silenciosamente crie claims, screening, RoB, certainty ou PRISMA.
- Adicionado `/synthesis-brief.html` como **Human Synthesis Brief**, que importa a revisão humana somente no navegador e libera apresentação/export apenas após validar tipo do artefato, semântica humana, content SHA-256 e correspondência do context fingerprint com o Article 1 atual.
- O Brief rejeita decisões duplicadas, pares inválidos, snapshots sem bundle/result text e artefatos cujos guardrails não confirmem explicitamente que relações foram human-entered e que nenhum EvidenceClaim, screening, RoB, certainty, PRISMA ou formal-search state foi criado.
- `NUTEV_HUMAN_SYNTHESIS_BRIEF_V1` permanece `canonical:false`, preserva os julgamentos source-linked, produz SHA-256 próprio e oferece Print/PDF para apresentação executiva sem converter contagens de relações em evidence strength, meta-analysis ou certainty.
- A documentação/UI agora explicita que SHA-256 verifica consistência/integridade de conteúdo, mas **não prova autoria, autenticidade da identidade do revisor nem validade científica**.
- A CI passou a executar `node --check` também em `synthesis-brief.js`, e a suíte/death test cobrem a cadeia `Scientific Intelligence -> Human Synthesis Review -> Human Synthesis Brief`.
- Adicionado `/synthesis-governance.html` como **Synthesis Governance Registry**, uma superfície de coordenação local-only para registrar Briefs verificados sem converter importação em aprovação automática.
- O registry persiste o Brief pelo `content_sha256` e mantém entradas metadata-only com estados `STAGED`, `APPROVED_FOR_GOVERNED_USE` e `REJECTED_BY_GOVERNANCE`; staging repetido do mesmo Brief é idempotente.
- Os endpoints `GET /api/synthesis/governance`, `POST /api/synthesis/governance/stage` e `POST /api/synthesis/governance/decide` exigem loopback; o limite ampliado de 2 MiB é aplicado somente aos payloads de governance, mantendo 256 KiB como padrão da API.
- O servidor revalida tipo, guardrails, decisões humanas, `content_sha256`, `source_context_fingerprint`, search id, context version e pergunta antes do staging; ele não confia na validação browser-side do Brief.
- Aprovação/rejeição exige nome do responsável e justificativa mínima, reabre o Brief imutável no artifact store e revalida fonte/contexto no momento da decisão. Mudança do Workbench após staging bloqueia a decisão.
- `APPROVED_FOR_GOVERNED_USE` é explicitamente governance approval, não certainty, RoB, EvidenceClaim, meta-analysis, PRISMA ou canonical scientific synthesis; todas as entradas mantêm `canonical_scientific_synthesis_created:false`.
- O registry registra que reviewer/governor names não são identidades criptograficamente autenticadas nesta fase.
- Adicionado `tools/audit_synthesis_governance.py`; o job de guardrail do CI passou a executar o death test de governance além do Scientific Workspace death test, e o lint verifica a sintaxe de `synthesis-governance.js`.
- Adicionado `/synthesis-release.html` como **Governed Synthesis Release**, uma superfície local-only que permite preparar disseminação apenas a partir de registry entries `APPROVED_FOR_GOVERNED_USE` com aprovação humana explícita.
- A preparação reabre o Brief persistido e revalida novamente content SHA-256, context fingerprint, search id/context version/pergunta e os guardrails do Brief no momento do release; aprovação sob contexto antigo não é grandfathered para disseminação.
- O package `NUTEV_GOVERNED_SYNTHESIS_RELEASE_V1` permanece `canonical:false`, preserva decisões humanas source-linked, governor/reviewer/preparer provenance e purpose declarado, e recebe SHA-256 determinístico próprio.
- Releases são persistidos em `project_output_reference/scientific/synthesis_releases/` com package integral e record metadata-only; repetir a mesma preparação é idempotente pelo package hash.
- O release record é canônico apenas como trilha operacional (`canonical_release_record:true`), mantendo `release_package_canonical:false` e `canonical_scientific_synthesis_created:false`.
- O package explicita `accepted_evidence_claims_created:false`, `risk_of_bias_assessed:false`, `certainty_assessed:false`, `meta_analysis_performed:false`, `prisma_event_emitted:false` e `formal_search_state_changed:false`.
- Adicionado `tools/audit_governed_synthesis_release.py`; o CI passa a executar um terceiro death test e `node --check` para `synthesis-release.js`, protegendo o fluxo `Review -> Brief -> Governance -> Release` contra auto-release, stale context, canonização científica ou fake certainty/meta-analysis/PRISMA.
- Adicionado `/synthesis-publication.html` como **Governed Publication Manifest**, transformando um Governed Release revalidado em citation bundle e `PUBLICATION_STATEMENT_CANDIDATE` sem aceitar scientific claims automaticamente.
- A Fase 15 reutiliza o coordenador local-only do Governed Release: `POST /api/synthesis/releases/prepare` recebe a operação explícita `PREPARE_PUBLICATION_MANIFEST`, evitando uma nova superfície de escrita remota; `GET /api/synthesis/releases` inclui apenas publication records metadata-only.
- Antes de preparar o manifest, o serviço verifica o release record/package, recalcula o release SHA-256 e reconstrói o Governed Release contra governance, Brief e contexto atuais; stale release ou package adulterado falham fechado.
- O citation bundle preserva document id, title, identificadores disponíveis, bundle id, `source_sentence_sha256`, result text e demais campos source-linked já presentes; metadados bibliográficos ausentes não são inventados.
- `NUTEV_PUBLICATION_STATEMENT_CANDIDATE_V1` descreve somente o julgamento humano registrado (`classified by the reviewer as ...`), permanece `CANDIDATE_ONLY`, `accepted_evidence_claim:false`, `machine_inferred_scientific_claim:false` e exige edição/autoria humana.
- `NUTEV_GOVERNED_PUBLICATION_MANIFEST_V1` permanece `canonical:false` e explicita que não cria EvidenceClaims aceitos, RoB, certainty, meta-analysis, PRISMA, formal-search mutation, recomendação clínica ou identidade autenticada.
- Publication manifests são persistidos em `project_output_reference/scientific/publication_manifests/` com manifest integral e record metadata-only; preparação repetida é idempotente pelo manifest content hash.
- Adicionado `tools/audit_governed_publication_manifest.py`; o CI passa a executar um quarto death test e `node --check` para `synthesis-publication.js`, protegendo a cadeia `Review -> Brief -> Governance -> Release -> Publication Manifest` contra stale publication, claim promotion e perda de provenance.
- Adicionado `/evidence-claims.html` como **EvidenceClaim Review & Promotion**, a primeira superfície autorizada a criar um `EvidenceClaim` canônico, exclusivamente após revisão humana claim-by-claim de uma citation atômica.
- Pairwise synthesis statements (`CONVERGENT`, `DIVERGENT`, etc.) permanecem contexto de síntese e são explicitamente `directly_promotable_to_evidence_claim:false`; cada claim candidate deriva de uma única citation/source snapshot ligada a um único `EvidenceRecord`.
- `ACCEPT` exige reviewer, rationale, statement escrito pelo humano, confirmação de source attribution e confirmação da fronteira científica; o claim statement inicia vazio e o `result_text` não é copiado automaticamente para o campo canônico.
- Antes de aceitar, o sistema exige que `evidence:{document_id}` exista realmente em `project_output_reference/scientific/evidence_records.jsonl` e que seu `document_id` corresponda à citation; um id apenas derivado não satisfaz o gate.
- O gate referencial de `ACCEPT` ocorre antes da persistência do review através do coordenador local-only, impedindo que uma tentativa bloqueada por EvidenceRecord ausente deixe um artefato de aceitação ambíguo.
- `REVISE` é não final; `REJECT` é final sem claim; somente `ACCEPT` cria `NUTEV_CANONICAL_EVIDENCE_CLAIM_RECORD_V1` com `claim_semantics: SOURCE_REPORTED_PROPOSITION` e provenance até manifest/citation/bundle/source sentence.
- O accepted claim é canônico apenas como registro da proposição source-level aceita: mantém `screening_eligibility_verified:false`, `claim_evaluation_created:false`, `risk_of_bias_assessed:false`, `certainty_assessed:false`, `evidence_set_created:false`, `clinical_recommendation_created:false`, `meta_analysis_performed:false` e `prisma_event_emitted:false`.
- A decisão de claim revalida novamente Publication Manifest -> Governed Release -> governance/Brief/context no momento da decisão; contexto stale bloqueia ACCEPT/REJECT/REVISE em vez de grandfathering silencioso.
- A Fase 16 reutiliza os endpoints loopback-only `GET /api/synthesis/releases` e `POST /api/synthesis/releases/prepare`, com operações explícitas `STAGE_EVIDENCE_CLAIM_REVIEW` e `DECIDE_EVIDENCE_CLAIM`; nenhuma nova rota remota de escrita foi criada.
- Adicionados `nutev_tests/test_evidence_claim_review.py`, `nutev_tests/test_evidence_claim_review_web_contract.py` e `tools/audit_evidence_claim_review.py`; o CI passa a executar um quinto death test e `node --check` para `evidence-claims.js`.

### Documentação e governança

- README principal reescrito a partir do comportamento real da `main`.
- POP operacional consolidado para instalação, atualização, execução, retomada, validação e registro de runs.
- Arquitetura e pesos reais do ranking documentados em `docs/ARCHITECTURE.md`.
- Limitações conhecidas documentadas em `docs/KNOWN_LIMITATIONS.md`.
- Documentação de providers alinhada aos perfis `operational` e `deep`.
- Templates de issue/PR e políticas do repositório alinhados ao escopo atual do Reference Engine.
- Documentação de segurança corrigida para refletir `project_output_reference` e o fato de que `.env` não é carregado automaticamente.
- Documentado o contrato do Quality Observatory e do Scientific Workspace death test em `docs/QUALITY_OBSERVATORY.md`.
- Documentado o contrato da Scientific Intelligence / Synthesis Layer em `docs/SCIENTIFIC_INTELLIGENCE.md`.
- Documentado o fluxo de adjudicação humana e export não canônico em `docs/HUMAN_SYNTHESIS_REVIEW.md`.
- Documentado o contrato de verificação, context fingerprint, fronteira criptográfica e export executivo em `docs/HUMAN_SYNTHESIS_BRIEF.md`.
- Documentado o registry servidor-local, estados de governance, idempotência, revalidação no momento da decisão e fronteira `governance approval != scientific canonization` em `docs/SYNTHESIS_GOVERNANCE_REGISTRY.md`.
- Documentado o pacote de disseminação governada, persistência/idempotência, revalidação pós-approval e fronteira `governed release != scientific validation` em `docs/GOVERNED_SYNTHESIS_RELEASE.md`.
- Documentado o publication manifest, citation bundle, statement candidates, reutilização do coordenador local-only e fronteira `publication preparation != EvidenceClaim acceptance` em `docs/GOVERNED_PUBLICATION_MANIFEST.md`.
- Documentado o gate humano de EvidenceClaim, atomicidade por EvidenceRecord, integridade referencial e fronteira `claim acceptance != validity/certainty/inclusion` em `docs/EVIDENCE_CLAIM_REVIEW.md`.

### Correções incorporadas desde v1.0.0

- Perfil de coleta `operational` passou a ser o padrão para a primeira execução, mantendo os limites maiores via `NUTEV_DEEP_COLLECTION=1`.
- O terminal passou a exibir perfil e limites antes da coleta de rede.
- HTTP `401`/`403` nas interfaces nativas LILACS/BVS e SciELO passou a ser tratado como estado explícito `unavailable` em vez de falha fatal da rota latino-americana.
- Uma execução real no Windows foi registrada com status `COMPLETE`, 8.702 entradas no ranking, 115 grupos de taxonomia e TOP 100.
- DOI real da versão 1.0.0 foi registrado na documentação/citação após a publicação do arquivo Zenodo, sem mover a tag.
- A release `v1.1.0` foi publicada no GitHub em 12/09/2026 no commit imutável `49588233ad2828b8fcc6140398ab55aedf7c03ef` após os gates de release, deploy e auditoria pós-deploy.
- O arquivamento Zenodo/DOI da `v1.1.0` permanece externo e fail-closed até existir um registro real; o DOI de `v1.0.0` não é reutilizado.

## [1.0.0] - 2026-08-18

### Produto

- Estabelecida a identidade **NutEV Reference Engine**.
- Definido o fluxo suportado:

```text
SEARCH -> NORMALIZE -> DEDUPLICATE -> RANK -> EXPORT
```

- Repositório reduzido ao escopo de descoberta, normalização, deduplicação por identidade, ranking e exportação de referências.
- Removidas superfícies antigas de revisão científica, orquestração, UI/API, OCR/full text e análise que não pertenciam ao produto final suportado.

### Providers

- PubMed.
- Europe PMC.
- OpenAlex.
- Crossref.
- DOAJ.
- Semantic Scholar.
- Fontes oficiais/institucionais configuradas.
- LILACS/BVS nativo.
- SciELO nativo.
- Google Programmable Search, Brave e SerpAPI quando configurados.

Scopus e Web of Science não são simulados.

### Ranking

- Carregamento de todos os arquivos `keyword_taxonomy*.json`.
- Focus keywords configuráveis.
- Pesos por provider.
- Sinais textuais de tipo documental.
- Bônus por presença de DOI/PMID/PMCID.
- Bônus leve de recência.
- Ordenação estável para os mesmos registros/configuração.
- Faixas A/B/C como prioridade de leitura.

### Deduplicação

- Regra de identidade baseada, em ordem, em DOI, PMID, URL e título normalizado.
- Preferência pela versão com texto descritivo mais rico quando a identidade coincide.

Essa regra não equivale a deduplicação semântica completa.

### Outputs

- `TOP_REFERENCIAS.md`.
- `reference_ranking.csv`.
- `reference_ranking.jsonl`.
- `latest.json`.

### Release e arquivo

- Versão: `1.0.0`.
- Tag publicada: `v1.0.0`.
- Release commit: `5728d79b05e618897f01ba93886a17584c9f215f`.
- GitHub Release publicada em 18/08/2026.
- Zenodo record: `21998607`.
- DOI da versão: `10.5281/zenodo.21998607`.

O DOI foi incorporado à documentação corrente após a criação real do registro Zenodo; a tag `v1.0.0` permaneceu imutável.

[Unreleased]: https://github.com/WillianVagner123/NutEV-Evidence-Engine/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/WillianVagner123/NutEV-Evidence-Engine/releases/tag/v1.1.0
[1.0.0]: https://github.com/WillianVagner123/NutEV-Evidence-Engine/releases/tag/v1.0.0
