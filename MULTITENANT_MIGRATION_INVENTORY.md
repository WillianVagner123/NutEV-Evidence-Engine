# Nut Evidence Platform — Multi-tenant Migration Inventory

**PR-0 — INVENTÁRIO · sem alteração comportamental**

- Baseline auditada: `main@3cfc3d922cc9e74017a9d8d710f055dd742c3dc8`
- Objetivo: registrar a arquitetura, ownership, storage, autenticação e fronteiras de dados existentes antes de introduzir identidade multiusuário.
- Regra deste PR: **não migrar dados, não executar buscas, não alterar IDs científicos, não recalcular resultados, não alterar ranking, não recriar PRISMA e não mudar comportamento de produção.**
- O patrimônio em `project_output*` é ignorado pelo Git e, portanto, o conteúdo real do volume de produção não é inferido a partir do clone.

## 1. Legenda de ownership

| Classe | Significado |
|---|---|
| `GLOBAL` | conhecimento bibliográfico/técnico público reutilizável entre workspaces |
| `WILLIAN_PRIVATE` | estado científico privado de Willian sem vínculo inequívoco com A1/A2 ainda |
| `ARTICLE1_PRIVATE` | estado científico específico do Artigo 1 |
| `ARTICLE2_PRIVATE` | estado científico específico do Artigo 2 |
| `SYSTEM` | infraestrutura, configuração operacional, build, logs técnicos sem estado científico privado |
| `UNKNOWN` | ownership/redistribuição não demonstrados; **não migrar automaticamente** |

Não existe classe `MIXED` para migração. Quando um artefato físico mistura conteúdo global e privado ele é decomposto logicamente em linhas distintas; o contêiner físico permanece `UNKNOWN` até que essa decomposição possa ser provada sem perda de estado.

---

## 2. Fontes inspecionadas

Inventário construído a partir de:

- `AGENTS.md`
- `AI_CONTEXT.md`
- `docs/ARCHITECTURE.md`
- `apps/nutev-web/server.py`
- `apps/nutev-web/secure_server.py`
- `apps/nutev-web/search_access.py`
- `apps/nutev-web/search_adapter.py`
- `apps/nutev-web/article_workbench_data.py`
- `apps/nutev-web/validation_server.py`
- `src/nutev/registry/`
- `src/nutev/science/`
- `ARTICLE1_SEARCH_MASTER.md`
- `docs/NUTEV_SEARCH_TO_BANK.md`
- `.gitignore`
- `deploy/hetzner/Dockerfile`
- `deploy/hetzner/compose.yaml`
- `deploy/hetzner/Caddyfile`
- busca de dependências `article1`, `article2`, `Artigo 2`, `busca2a`, `busca2b` no estado atual da `main`.

O conteúdo real do volume Docker `nutev_output` não é versionado no Git e continua exigindo inspeção runtime somente-leitura.

---

# 3. MATRIZ — ÁREA ATUAL × OWNERSHIP × TENANCY

| Área atual | Classe | Precisa de tenant? | Risco | Decisão PR-0 |
|---|---|---:|---|---|
| `src/nutev/search/` providers e adapters genéricos | `SYSTEM` | não para lógica; sim no request | baixo | preservar como Engine reutilizável |
| taxonomia canônica e regras genéricas de normalização | `GLOBAL`/`SYSTEM` conforme arquivo | não | baixo | preservar; não acoplar a usuário |
| Registry `articles` — identidade/título/autores/journal/ano/public abstract | `GLOBAL` | não | médio | manter como Global Evidence Registry |
| Registry `article_aliases` | `GLOBAL` | não | baixo | manter global |
| Registry `article_manifestations` de metadados públicos | `GLOBAL` | não | médio | manter global; revisar payload bruto antes de declarar redistribuível |
| Registry `article_field_history` de metadados públicos | `GLOBAL` | não | médio | manter global quando campo/origem forem públicos |
| Registry `search_runs.query` e estratégia/provider plan | `UNKNOWN` | **sim** | crítico | não tratar como global; ownership precisa ser resolvido |
| Registry `search_hits` | `UNKNOWN` | **sim** | alto | relação de execução deve ganhar owner/contexto; não confundir com identidade global |
| Registry `identity_conflicts` | `SYSTEM`/`GLOBAL` | não | médio | global se restrito a identidade bibliográfica |
| Registry `full_text_artifacts` | `UNKNOWN` | **sim** para grants | crítico | separar identidade/hash de `FullTextAccessGrant`; auditar direitos |
| Registry `core_versions.record_json` | `UNKNOWN` | possivelmente | alto | auditar conteúdo antes de classificar; hashes/proveniência podem ser globais, derivação científica pode não ser |
| `15_web_searches/<search_id>/result.json` | `UNKNOWN` | **sim** | crítico | preservar; atribuir owner apenas por migração demonstrada |
| `15_web_searches/.ownership.json` | `SYSTEM` legado | substituir | alto | browser-session ownership não é identidade científica |
| `_SEARCH_JOBS` em memória | `SYSTEM` com estado privado transitório | **sim** | crítico | evoluir para `workspace_id/user_id/project_id/job_id` autorizado |
| `bank/searches/<search_id>/` | `UNKNOWN` | **sim** | alto | per-search; não migrar até owner ser demonstrado |
| `scientific/document_candidates.jsonl` | `UNKNOWN` | sim se houver state derivado | alto | auditar campos |
| `scientific/evidence_records.jsonl` | `UNKNOWN` | **sim** | crítico | conteúdo científico derivado não deve cruzar tenant sem contrato explícito |
| `scientific/enrichment/` | `UNKNOWN` | sim | crítico | separar metadata pública de full text/acesso privado |
| `scientific/core/` | `UNKNOWN` | sim | alto | preservar hashes; auditar conteúdo científico |
| `scientific/semantic/` | `WILLIAN_PRIVATE` ou projeto específico a demonstrar | **sim** | crítico | não globalizar candidatos/leituras científicas |
| `scientific/excerpts/` | `WILLIAN_PRIVATE` ou projeto específico a demonstrar | **sim** | crítico | privado por padrão |
| `scientific/workbench/evidence_workbench.sqlite` — metadados bibliográficos | `GLOBAL` logicamente | não | médio | somente a fatia bibliográfica pode alimentar Registry global |
| Workbench — rank/tier/machine relevance | `WILLIAN_PRIVATE`/`UNKNOWN` | **sim** | crítico | não expor entre tenants; não é decisão científica, mas é state privado de processamento |
| Workbench — `evidence_excerpts` e `result_bundles` | `WILLIAN_PRIVATE`/`UNKNOWN` | **sim** | crítico | privado; artefato físico permanece UNKNOWN até split seguro |
| `16_validation_server/validation.sqlite3` | `WILLIAN_PRIVATE`/projeto a demonstrar | **sim** | crítico | migrar por referência para HumanReviewEngine; não fundir destrutivamente |
| `validation_reviewers.token` atual | `SYSTEM` secret | escopo obrigatório | crítico | **não copiar modelo bruto**; novo sistema armazena hash + expiração + revogação |
| `agent_context/article1/*` | `ARTICLE1_PRIVATE` por default no modelo alvo | **sim** | crítico | atual bundle rank-blind não implica publicação; mover para visibilidade explícita |
| `scientific/review_routes/<search_id>/article1/` | `ARTICLE1_PRIVATE` | **sim** | crítico | preservar por referência/hash |
| `ARTICLE1_SEARCH_MASTER.md` e config A1 | `ARTICLE1_PRIVATE` do ponto de vista de projeto, embora parte esteja versionada | **sim** | alto | usar como source of truth de migração; não reexecutar |
| `src/nutev/science/article1_*` | `ARTICLE1_PRIVATE` application-specific code/config | via aplicação | médio | progressivamente virar cliente de primitives; não refatorar destrutivamente |
| `tools/*article1*` | `ARTICLE1_PRIVATE` application tooling | via aplicação | médio | preservar durante migração |
| `article2` first-class namespace no repo | `UNKNOWN` | **sim** | crítico | **não localizado na main**; runtime/legado deve ser inventariado antes de migrar |
| `workstreams.busca2a/busca2b` em taxonomias históricas | `UNKNOWN` | sim se forem state de A2 | alto | não presumir equivalência com Artigo 2; apenas vestígio histórico |
| `deploy/hetzner/compose.yaml`, Dockerfile, Caddy | `SYSTEM` | não | baixo | preservar como infraestrutura |
| volume `nutev_output:/app/project_output_reference` | `UNKNOWN` físico | **sim** | crítico | contém múltiplas classes; fazer inventário runtime read-only |
| Basic Auth do Caddy | `SYSTEM` perimeter | não substitui tenant | alto | pode permanecer como barreira temporária; nunca usar como identidade de workspace |

---

# 4. CURRENT_ARCHITECTURE

```text
Browser
  |
  |-- Caddy Basic Auth (perímetro único)
  v
SecureNutEVHandler
  |
  |-- cookie anônimo nutev_session
  |-- owner_scope = SHA256(cookie)
  |-- history/jobs filtrados por sessão do navegador
  |
  +--> search engine / 11 providers
  |      |
  |      +--> persisted web search
  |      +--> Article Registry (global físico, sem tenant)
  |
  +--> Articles API
  |      +--> hash-verified Workbench único
  |
  +--> Reviewer API
  |      +--> Bearer token
  |      +--> validation.sqlite3
  |
  +--> coordinator/scientific admin endpoints
         +--> autorização atual por loopback

Persistent volume único:
/app/project_output_reference
  |
  +-- 15_web_searches/
  +-- bank/searches/
  +-- registry/article_registry.sqlite
  +-- scientific/
  |    +-- enrichment/
  |    +-- core/
  |    +-- semantic/
  |    +-- excerpts/
  |    +-- workbench/
  |    +-- review_routes/.../article1/
  +-- 16_validation_server/validation.sqlite3
  +-- agent_context/article1/
```

## 4.1 O que já está bem separado

1. O motor de busca e providers são predominantemente genéricos.
2. O Article Registry já usa `article_id` durável, aliases, manifestações e histórico de campos.
3. SearchRuns/SearchHits já preservam proveniência da descoberta.
4. Full text e CORE já são vinculados ao `article_id` e versionados/hashing.
5. `src/nutev/science/__init__.py` já expõe primitives científicos genéricos como `ResearchQuestion`, `EvidenceSet`, `FullTextArtifact`, `ScreeningDecision`, `EvidenceClaim`, `ScientificEvent` e outros.
6. O reviewer atual já possui assignments, autosave, submission lock e audit events.
7. Produção já possui cookie HttpOnly/SameSite/Secure e CSP/headers, mas esse cookie representa sessão anônima, não usuário autenticado.

## 4.2 O que ainda é single-operator/single-workspace

1. Não existem `User`, `Workspace`, `Membership`, `Project`, `ResearchApplication` ou `Principal` de plataforma.
2. `search_runs` não tem `workspace_id`/`project_id`.
3. jobs em memória não carregam owner científico.
4. histórico público é isolado por browser session, não por conta/workspace.
5. Articles/Workbench usam um índice único e não filtram placement privado por workspace/projeto.
6. coordenação usa `loopback` como autorização.
7. o volume persistente é único e não possui namespace lógico `private_data/workspaces/<workspace_id>/...`.
8. Article 1 aparece diretamente em código, paths, contexto web e startup do container.

---

# 5. CURRENT ACCESS SURFACE

Esta tabela descreve **autorização da aplicação**, não a barreira externa do Caddy Basic Auth.

| Endpoint/superfície | Controle atual | Estado alvo |
|---|---|---|
| `GET /api/health` | aberto na app | `SYSTEM`, sem segredo |
| `GET /api/version` | aberto na app | `SYSTEM`, sem segredo |
| `GET /api/providers` | aberto na app | global/público |
| `GET /api/capabilities` | aberto na app | `SYSTEM` |
| `POST /api/query/compile` | sem Principal | permitir conforme política; não persistir privado sem owner |
| `POST /api/search/jobs` | sessão anônima + rate limit | `Principal` + `workspace` + permission `search.run` |
| `GET /api/search/jobs/<job_id>` | owner hash da browser session | validar Principal + workspace/project access |
| `GET /api/searches*` | owner hash da browser session | escopo My Workspace / Project Searches |
| `GET /api/articles*` | sem tenant na app | GlobalDocument + Placement/field policy conforme contexto |
| `GET /api/radar` | sem tenant na app | privado/tenant-scoped se contiver state de projeto |
| `GET /api/validation/readiness` | sem tenant na app | projeto/review scoped |
| reviewer GET/save/submit | Bearer token | Guest/Reviewer scope mínimo, token hash, expiração, revogação |
| synthesis/governance/admin scientific endpoints | loopback | Principal + Permission Service; loopback apenas compatibility flag temporária |
| adjudication/gold/metrics/lock | loopback | projeto + role/permission explícita |
| `/agent-context/article1/*` | static bundle quando materializado | `ARTICLE1_PRIVATE` por padrão; visibilidade explícita se publicada no futuro |

**Conclusão:** o `secure_server.py` melhora isolamento entre navegadores, mas não constitui multi-tenancy. Conhecer/possuir um cookie de browser não equivale a ser membro de um workspace.

---

# 6. CURRENT SEARCH STATE

## 6.1 Search Engine

A busca interativa possui 11 providers canônicos e persiste cada execução em:

```text
project_output_reference/15_web_searches/<search_id>/result.json
```

A persistência registra o resultado também no Article Registry cumulativo.

### Gap de ownership

Hoje existem duas identidades diferentes e insuficientes para multi-tenancy:

```text
search_id
browser-session owner_scope
```

O contrato alvo exige:

```text
user_id
workspace_id
project_id?  # optional for free workspace/library search
job_id
search_id
```

A migração não pode inferir `workspace_id` a partir de `search_id`, query ou nome de pasta.

## 6.2 Historical search ownership

Searches já existentes precisam de `LEGACY_MIGRATION_MANIFEST`/mapping explícito. Runs sem origem inequívoca ficam `UNKNOWN` e não são anexados automaticamente a A1/A2.

---

# 7. CURRENT GLOBAL REGISTRY

O Registry atual é o melhor candidato a permanecer como núcleo global, mas **não todas as tabelas têm semântica global**.

## 7.1 Pode permanecer global após validação de campos

```text
articles
article_aliases
article_manifestations (public bibliographic manifestations)
article_field_history (public bibliographic fields)
identity_conflicts (bibliographic identity only)
```

## 7.2 Precisa de fronteira privada

```text
search_runs
search_hits
full_text_artifacts access/redistribution state
core_versions when record_json contains project-derived state
```

### Regra de migração

`article_id` não deve mudar para criar tenancy. A tenancy deve ser adicionada **ao redor da identidade global**, por relações privadas como `project_documents`, search ownership, grants e scientific state.

---

# 8. CURRENT WORKBENCH

O Workbench único contém mais de uma categoria lógica:

```text
ArticleEvidenceCard / bibliographic fields
reference_rank / reference_score / reference_tier
review_profile
machine_relevance
EvidenceExcerpt
ResultBundle
```

Por isso, `evidence_workbench.sqlite` **não pode ser declarado inteiro como GLOBAL**.

Plano de boundary futuro:

```text
GlobalDocument identity/public metadata
          |
          +--> private Placement
          +--> private ranking/navigation state when project-specific
          +--> private excerpts/result bundles/decisions
```

Nenhuma divisão física será executada no PR-0.

---

# 9. CURRENT VALIDATION / REVIEWER MODEL

A implementação atual já oferece conceitos aproveitáveis:

- `validation_rounds`
- reviewers
- assignments
- autosave
- submission
- lock
- audit events
- blind flag

Mas o schema atual guarda `token` bruto em `validation_reviewers` e o status administrativo consegue lê-lo. O alvo **não deve copiar esse armazenamento**.

Contrato futuro mínimo:

```text
ReviewRound
Reviewer/GuestPrincipal
Assignment
Decision
Submit
Lock
Adjudication
```

com:

```text
token_hash
expires_at
revoked_at/scope
workspace_id
project_id
round_id
```

A migração deverá preservar a validação atual operacional até o HumanReviewEngine estar comprovadamente equivalente.

---

# 10. ARTICLE 1 INVENTORY

## 10.1 Estado canônico conhecido

`ARTICLE1_SEARCH_MASTER.md` registra:

```text
DISCOVERY_CLOSED_FORMAL_SEARCH_PENDING_PRESS_FREEZE
```

A discovery histórica está preservada, mas a formal search não foi executada; PRESS não está PASS e GF-10 não está autorizado.

Isso é um guardrail de migração: **nenhuma mudança multi-tenant pode transformar discovery em formal search, inclusão ou PRISMA.**

## 10.2 Dependências específicas localizadas

Principais namespaces/artefatos específicos localizados no repo:

```text
ARTICLE1_SEARCH_MASTER.md
config/nutev/article1_search_master_v1.json
config/nutev/article1_query_draft_v1.json
config/nutev/topic_profiles/article1_prefreeze_v1.json
src/nutev/science/article1_agent_context.py
src/nutev/science/article1_press.py
src/nutev/science/article1_routes.py
src/nutev/science/article1_vocabulary.py
tools/build_article1_agent_context.py
tools/build_article1_route_queues.py
tools/audit_article1_route_vocabulary.py
tools/build_article1_press_query_package.py
tools/build_article1_press_human_review_packets.py
tools/extract_article1_press_human_review_samples.py
apps/nutev-web/agent-context/article1 -> runtime symlink
deploy startup -> build_article1_agent_context.py
```

E runtime authorities declaradas:

```text
scientific/deepening/<search_id>/tier-A/
scientific/review_queue/<search_id>/tier-A/
scientific/review_routes/<search_id>/article1/
scientific/workbench/
agent_context/article1/
```

## 10.3 Target ownership

```text
Willian
└── Workspace: Doutorado Willian — UnB
    └── Project: Artigo 1
        └── ResearchApplication: SCOPING_REVIEW
```

O PR-7 deverá migrar ownership por referência/hash. Não mover ou reprocessar esse patrimônio no PR-0.

---

# 11. ARTICLE 2 INVENTORY

## 11.1 Finding

Não foi localizado na `main` um namespace first-class `article2`, nem `INTEGRATIVE_REVIEW` associado a uma aplicação concreta do Artigo 2.

Existem vestígios históricos como:

```text
workstreams.busca2a
workstreams.busca2b
```

em taxonomias/configurações antigas. Esses nomes **não provam** que o conteúdo corresponde ao patrimônio canônico do Artigo 2.

## 11.2 Classificação

```text
ARTICLE2_RUNTIME_STATE = UNKNOWN
```

Até inspeção runtime, é proibido:

- anexar `busca2a/busca2b` automaticamente ao Artigo 2;
- mover arquivos por semelhança nominal;
- recalcular PILOT/query counts;
- fundir com Artigo 1;
- preencher lacunas usando memória ou inferência.

## 11.3 Target ownership planejado, ainda não ativado

```text
Willian
└── Workspace: Doutorado Willian — UnB
    └── Project: Artigo 2
        └── ResearchApplication: INTEGRATIVE_REVIEW
```

O `project_id`/`application_id` só será criado na migração de ownership depois que a fonte runtime for inventariada e hashada.

---

# 12. CURRENT PRODUCTION PATHS

## 12.1 Container

```text
/app
/app/project_output_reference
/app/apps/nutev-web
```

## 12.2 Volume

Compose declara:

```text
nutev_output:/app/project_output_reference
```

Logo, todo o estado persistente relevante está hoje atrás de um único volume lógico.

## 12.3 Article 1 static bridge

O Dockerfile cria:

```text
/app/apps/nutev-web/agent-context/article1
  -> /app/project_output_reference/agent_context/article1
```

Isso é uma dependência first-party do Artigo 1 no produto hospedado e deverá ser migrada para routing/contexto de projeto, sem quebrar o legado durante a transição.

## 12.4 Git boundary

`.gitignore` exclui:

```text
project_output*/
```

Portanto, o repositório não é fonte suficiente para enumerar o patrimônio real do volume. A inspeção runtime deve ser read-only e produzir hashes/inventory antes do PR-7.

---

# 13. TARGET_ARCHITECTURE

```text
                         +-------------------------+
                         |   Authentication        |
                         +------------+------------+
                                      |
                                   Session
                                      |
                                  Principal
                                      |
                            Permission Service
                                      |
          +---------------------------+--------------------------+
          |                                                      |
          v                                                      v
+----------------------+                              +----------------------+
| Workspace/Project    |                              | Global Evidence      |
| private state        |                              | Registry             |
+----------+-----------+                              +----------+-----------+
           |                                                         |
 User -> Workspace -> Project -> ResearchApplication                 |
           |                                                         |
           +---- project_documents -----------------> GlobalDocument |
           +---- searches/search jobs ------------------------------>|
           +---- screening/extraction/review private                 |
           +---- FullTextAccessGrant ------------------------------->|
           +---- export/audit private                                |

Scientific Engine primitives remain reusable and user-agnostic.
```

Principle:

```text
The Nut Evidence Engine knows scientific operations, not individual manuscripts.
```

A1 e A2 passam a ser **assemblies/applications privadas** que configuram primitives do mesmo Engine.

---

# 14. MIGRATION_GAPS

| Gap | Severidade | PR alvo |
|---|---:|---|
| inexistência de User/Workspace/Membership/Project/Principal | crítica | PR-1 |
| auth/session ainda anônima em produção | crítica | PR-2 |
| loopback usado como autorização científica | crítica | PR-2/PR-3 |
| Permission Service inexistente | crítica | PR-1/PR-3 |
| search run sem workspace/project owner | crítica | PR-4 |
| jobs em memória sem tenant identity | crítica | PR-4 |
| Evidence Library inexistente | alta | PR-5 |
| Placement privado sobre GlobalDocument inexistente | crítica | PR-5 |
| ResearchApplication/ApplicationTemplate first-class inexistentes | alta | PR-6 |
| patrimônio Willian não possui ownership explícito | crítica | PR-7 |
| Artigo 2 runtime não materializado no repo | crítica | PR-7/PR-10 |
| review atual acoplado a validation schema/token bruto | crítica | PR-8 |
| A1 possui módulos/path/startup específicos | alta | PR-9 |
| export multi-tenant inexistente | alta | PR-11 |
| tenant death test inexistente | crítica | PR-12 |
| volume persistente físico não separado por workspace | alta | migração progressiva após contratos |

---

# 15. SECURITY_GAPS

1. **Authentication gap:** Caddy Basic Auth protege o perímetro, mas não identifica workspace/project.
2. **Anonymous session gap:** `nutev_session` isola navegador, não pessoa/tenant.
3. **Loopback authorization:** local address funciona como privilégio administrativo para endpoints científicos.
4. **IDOR risk in base handler:** jobs/search IDs são suficientes no handler base; produção adiciona browser-session scope, mas não membership scope.
5. **Unscoped article surface:** Articles/Workbench não possuem field-level tenant authorization.
6. **Guest token storage:** validation atual guarda token bruto; alvo deve armazenar hash.
7. **Field blinding:** backend precisa filtrar campos por policy; esconder no frontend não é suficiente.
8. **Single shared volume:** filesystem não oferece boundary de tenant hoje.
9. **Support access:** não existe `SupportAccessGrant`; futuro PLATFORM_ADMIN não deve implicar leitura científica privada.
10. **Revocation:** membership/session/guest revocation precisa falhar imediatamente no modelo alvo.

Nenhum desses gaps autoriza uma correção ampla no PR-0.

---

# 16. DATA_OWNERSHIP_GAPS

## 16.1 Search history

A associação histórica `search_id -> browser-session hash` não é suficiente para dizer “pertence a Willian/A1/A2”. Precisa de manifest de migração explícito.

## 16.2 Workbench

Um banco físico mistura metadados globalizáveis e state de processamento/review. Precisa de decomposição lógica comprovada.

## 16.3 Full text

Hash/identidade técnica podem ser reutilizáveis; **direito de acesso e redistribuição não é inferido do fato de o arquivo existir**.

## 16.4 Article 1

Ownership é conceitualmente claro, mas deve ser materializado por migration manifest e hashes, sem mover/reexecutar no primeiro passo.

## 16.5 Article 2

Ownership alvo é conhecido, porém a localização runtime canônica não foi demonstrada no repo. Estado = `UNKNOWN` até inspeção real.

## 16.6 Legacy scientific outputs

Artefatos sem owner inequívoco não serão “jogados” no workspace de Willian por default. Permanecem preservados e quarantined-from-migration até classificação explícita.

---

# 17. RUNTIME INVENTORY REQUIRED BEFORE OWNERSHIP MIGRATION

Executar futuramente, **read-only**, no volume real de produção e registrar sem conteúdo sensível bruto:

```text
path
object type
size
mtime
SHA-256
candidate ownership
reason/evidence
contains protected full text? yes/no/unknown
contains human decisions? yes/no/unknown
migration state
```

Escopo mínimo a localizar:

```text
15_web_searches/
bank/searches/
registry/
scientific/
16_search_full_text_cache/
16_validation_server/
agent_context/article1/
qualquer artifact A2/PILOT/query manifest não versionado
```

A saída deverá alimentar o futuro `LEGACY_MIGRATION_MANIFEST.json`. Nenhum `UNKNOWN` pode virar ACTIVE automaticamente.

---

# 18. PR-0 AUDIT REPORT

## Objetivo

Inventariar o estado atual e definir fronteiras de ownership/tenancy antes de qualquer código multiusuário.

## Arquivos alterados

```text
MULTITENANT_MIGRATION_INVENTORY.md
```

## Schema alterado

Nenhum.

## Riscos

Baixo risco de runtime: documentação apenas. Risco principal é classificação incorreta; por isso elementos não demonstrados permanecem `UNKNOWN`.

## Backwards compatibility

100%: nenhuma execução, rota, schema ou output é alterado.

## Security impact

Nenhuma mudança de enforcement. Gaps atuais foram explicitados para PRs posteriores.

## Scientific impact

Nenhuma mutação científica. A1 continua em `DISCOVERY_CLOSED_FORMAL_SEARCH_PENDING_PRESS_FREEZE`; nenhum PRESS/GF-10/formal search/PRISMA foi produzido.

## Tests

Este PR é docs-only. CI existente deve permanecer verde; não há justificativa para executar search/network ou materialização científica como teste deste diff.

## Death tests

Não aplicáveis como execução no PR-0. Casos necessários estão especificados para PR-4/PR-12.

## Migration impact

Nenhuma migração executada. Somente planejamento/classificação.

## Rollback plan

Reverter o commit documental. Não existe rollback de dados porque nenhum dado foi modificado.

---

# 19. PR-0 GATE

## Repositório

```text
PASS
```

para o objetivo de **inventário estático e definição das fronteiras**.

## Runtime historical ownership

```text
NOT_MATERIALIZED / UNKNOWN ITEMS REMAIN
```

Isso **não impede PR-1 de criar contratos vazios de identidade**, pois PR-1 explicitamente não migra dados. Porém bloqueia qualquer PR que tente atribuir/mover o patrimônio histórico de Willian/A1/A2 sem o inventory/hash runtime correspondente.

## Proibições que permanecem

```text
NO historical search rerun
NO A1/A2 reassignment by filename guess
NO Workbench global promotion
NO raw guest-token migration
NO PRISMA recreation
NO production data move
NO main direct edit
```

---

# 20. NEXT AUTHORIZED STEP

Após CI/review deste PR-0, o próximo escopo é **PR-1 — IDENTIDADE E CONTRATOS**, limitado a:

```text
User
Workspace
Membership
Project
ResearchApplication
Principal
Permission
Permission Service contracts
```

com testes de autorização e **sem migrar nenhum patrimônio existente ainda**.
