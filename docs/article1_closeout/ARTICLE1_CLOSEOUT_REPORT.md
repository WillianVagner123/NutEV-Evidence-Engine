# Article 1 / NutEV — Closeout Report

**Status:** `TECHNICAL_CLOSEOUT_PASS / REAL_USER_PRODUCTION_ACCEPTANCE_PENDING`  
**Runtime-closeout timestamp:** 2026-09-24 UTC  
**Scope:** produto hospedado + custódia operacional do Artigo 1. Este relatório **não** abre gate científico.

> O SHA abaixo é o **runtime-closeout SHA**: naquele ponto, `main` e produção coincidiam exatamente.
> A publicação posterior deste próprio relatório é metadata documental e não altera retrospectivamente
> a prova do runtime. Qualquer mudança posterior que afete runtime deve obter nova prova exact-SHA.

## 1. PRODUCT

| Item | Estado / evidência |
|---|---|
| Runtime-closeout main SHA | `8ad630ebb37474f9e1024b4858e57b7c51aa27ab` |
| Runtime-closeout production SHA | `8ad630ebb37474f9e1024b4858e57b7c51aa27ab` |
| Deploy | PASS — run `35937762124` |
| Production doctorate audit | PASS — run `35938246422` |
| Auth mode | `NUTEV_AUTH_MODE=pilot` |
| Workspace | `Doutorado — Willian Vagner` |
| Project | `Artigo 1` |
| Application | `SCOPING_REVIEW` |
| Owner role/binding | `WORKSPACE_OWNER`; `assembly_id=WILLIAN_DOCTORATE_A1` |
| Owner pins | `OWNER_PINS_MATCH`; sincronizados a partir de configuração protegida |
| CI | PASS — Python 3.12/3.13, Windows smoke, typecheck, lint, audit guardrail |
| Browser | PASS — Chromium product gate + Authenticated pilot browser closeout |
| Security | PASS — CodeQL, secret scanning, repository file-policy checks and dependency review |
| Multi-tenant | PASS — Full multi-tenant death test |
| Release/recovery | PASS — release artifact validation + production recovery readiness |
| Open PRs | nenhum no momento do runtime closeout |

### 1.1 Prova exact-SHA de produção

O deploy do SHA `8ad630ebb37474f9e1024b4858e57b7c51aa27ab` revalidou todos os pré-requisitos e terminou com:

```text
PUBLIC_HEALTH_STATUS=200
PUBLIC_VERSION_STATUS=200
PUBLIC_ROOT_STATUS=200

actual_commit =
8ad630ebb37474f9e1024b4858e57b7c51aa27ab

expected_commit =
8ad630ebb37474f9e1024b4858e57b7c51aa27ab

NUTEV_REMOTE_DEPLOY_COMPLETE
8ad630ebb37474f9e1024b4858e57b7c51aa27ab
```

A resposta final de `/api/version` identificou serviço `nutev-web`, versão `1.1.0`,
branch `main`, ambiente `production` e esse mesmo commit.

### 1.2 Runtime do doutorado

O audit read-only pós-deploy registrou:

```text
doctorate audit status: PASS
doctorate audit: 1 A1 app(s), 0 A2 app(s)
Article 1 runtime ready: True
Article 1 owner pins: OWNER_PINS_MATCH
```

O bootstrap de primeiro administrador também observou:

```text
platform_admin_state=READY
existing_admin_count=1
changed=false
```

Logo, nenhum bootstrap de identidade foi executado nessa promoção. O workflow permanece
como operação idempotente de contingência; não é evidência de criação de usuário ou estado científico.

### 1.3 Limite da prova autenticada

O pipeline autenticado de navegador passou no mesmo SHA e cobre login, seleção de workspace/projeto,
persistência de aplicação, isolamento, biblioteca, navegação, logout cross-tab e jornada de supervisor.

No runtime de produção, `/api/article1/scientific-state` e `/api/article1/d132/review` foram
confirmados como superfícies privadas fail-closed: sem sessão recebem `401`.

**Ainda não foi capturada nesta sessão uma requisição autenticada da conta real do usuário em produção
demonstrando `GET /api/article1/scientific-state -> 200`.** Isso permanece como aceitação manual de
última milha; não deve ser substituído por inferência a partir do `401`, do fixture ou do audit de banco.

## 2. ARTICLE 1

### 2.1 Estado científico canônico

```text
status = DISCOVERY_CLOSED_FORMAL_SEARCH_PENDING_PRESS_FREEZE
PRESS = NOT_YET_RECORDED_AS_PASS
GF-10 = false
query_freeze_complete = false
formal_provider_search_executed = false
prisma_search_event_emitted = false
C4 = PRESS_ONLY_CANDIDATE_NOT_APPROVED
```

Fechamento técnico do produto não altera esses valores.

### 2.2 Corpus / rotas — snapshot canônico de discovery

| Medida | Valor |
|---|---:|
| Registros antes da deduplicação | 41.139 |
| Referências únicas | 33.839 |
| Aceitos estruturalmente | 33.067 |
| Quarentena estrutural | 772 |
| Tier A | 662 |
| Retrieved + partial | 594 / 662 = 89,73% |
| B-NORM | 85 |
| C-STRUCT | 316 |
| União de rotas | 351 |
| Overlap | 50 |
| Unrouted | 311 |

Essas contagens representam discovery/deepening/navegação. Não são screening, inclusão,
exclusão, avaliação de qualidade ou PRISMA.

### 2.3 D-132 / Human Review

Custódia canônica em produção:

```text
d132_config_version = d132-v1
total = 100
D02 = 25
D03 = 25
D04 = 25
D05 = 25
custody = PASS
```

Contrato humano:

- decisão Y/N/U;
- dois revisores independentes por item;
- slots A/B;
- razão obrigatória;
- adjudicação humana;
- nenhuma promoção automática de PRESS, C4, GF-10, freeze, formal search ou PRISMA.

Limitação metodológica: D-132 v1 deriva de amostragem técnica com viés de recência observado.
Ele pode sustentar inspeção/revisão humana, mas não deve ser tratado como estimativa global de precisão
sem decisão humana sobre manter o pacote como exploratório ou especificar um D-132b aleatório/estratificado.

### 2.4 Human Review — estado

- engine/superfície existem e estão protegidos por autorização;
- D-132 canônico está materializado e íntegro;
- revisores independentes ainda não foram definidos;
- adjudicador ainda não foi definido;
- nenhuma decisão humana D-132 foi promovida a gate científico.

### 2.5 Full text

O snapshot estático registra:

- retrieved = 504;
- partial = 90;
- not retrieved = 68;
- retrieved + partial = 594 / 662 = 89,73%.

Recuperação de texto completo é auxílio operacional de leitura. Não equivale a inclusão,
elegibilidade, qualidade metodológica ou decisão científica.

### 2.6 Known items

Há 14 sentinelas de desenvolvimento versionadas. No snapshot descrito:

- 11/14 foram recuperadas por alguma rota;
- 10/14 pela rota esperada.

Pontos diagnósticos prioritários: KI03 (eating competence), KI08 (competências profissionais),
KI10 (food environments) e KI13 (Lifestyle Medicine / Healthy Nutrition).

Known items não são gold standard e não autorizam freeze sozinhos.

### 2.7 Delta tests

Worksheet canônico pré-freeze:

| ID | Teste | Estado |
|---|---|---|
| D01 | B-NORM baseline vs + `food based` | revisão humana pendente |
| D02 | B-NORM baseline vs + `healthy eating` | revisão humana pendente |
| D03 | C1 com vs sem `meal plan*` | revisão humana pendente |
| D04 | C3 standalone yield + precision sample | revisão humana pendente |
| D05 | C4 incremental yield + precision sample | revisão humana pendente |

A execução técnica persistida não é uma formal search.

### 2.8 Precision samples / S1–S6

O desenho DEVELOPMENT S1–S6 foi descrito, mas os arquivos não estão materializados no runtime/repo
como pacote canônico. Portanto:

```text
S1–S6 = PROTOCOL/SNAPSHOT DESCRIBED
FILES = NOT CANONICALLY MATERIALIZED
```

Se o desenho for aprovado, ele deve ser regenerado de forma determinística, versionada,
com denominadores, manifesto, hashes e packets cegos antes de qualquer julgamento Y/N/U.

## 3. SCIENTIFIC GATES

| Gate | Estado no closeout |
|---|---|
| Discovery | concluído |
| PRESS | **PENDENTE** — `NOT_YET_RECORDED_AS_PASS` |
| GF-10 | **NÃO AUTORIZADO** |
| Query freeze | **PENDENTE** |
| Formal provider search | **NÃO EXECUTADA** |
| Formal PRISMA search event | **NÃO CRIADO** |
| C4 | `PRESS_ONLY_CANDIDATE_NOT_APPROVED` |

Provider-native validation permanece pendente para PubMed, LILACS/BVS, SciELO, Scopus e Web of Science.
Scopus/WoS não podem ser simulados como se tivessem sido validados.

## 4. PENDING HUMAN DECISIONS

### Willian Vagner

1. definir dois revisores independentes e o adjudicador;
2. decidir se D-132 v1 fica apenas como verificação exploratória;
3. decidir se haverá D-132b aleatório/estratificado;
4. definir quem valida sintaxe nativa de Scopus/WoS;
5. definir revisor PRESS independente;
6. decidir se PRESS inclui revisão nativa de LILACS/BVS e SciELO;
7. decidir se S1–S6 será regenerado/versionado.

### Discussão com Dr. Caio Reis

1. parâmetros nutricionais: extração é suficiente ou exige rota própria;
2. decisão sobre C4;
3. lugar de `eating competence`;
4. trade-off sensibilidade × especificidade do B-NORM, especialmente `standard*`;
5. papel de vocabulário controlado/publication types;
6. assimetria de campos entre providers;
7. validar known items, especialmente KI13;
8. estratégia de literatura cinzenta para Guia Alimentar/FBDGs e outras diretrizes não indexadas.

## 5. CLOSEOUT VERDICT

```text
RUNTIME / INFRASTRUCTURE = PASS
EXACT-SHA PRODUCTION = PASS
D-132 CUSTODY = PASS
OWNER PINS = PASS
CI / SECURITY / BROWSER / RECOVERY = PASS
OPEN PR CLEANUP = PASS

REAL-USER AUTHENTICATED PRODUCTION ACCEPTANCE = PENDING
ARTICLE 1 FORMAL SEARCH READINESS = HUMAN-GATED / NOT YET AUTHORIZED
```

Não existe blocker técnico conhecido no runtime-closeout SHA. O único item de aceitação funcional
não reproduzido diretamente nesta sessão é a jornada autenticada da conta real em produção.

## 6. NEXT ACTION

**Uma única próxima ação concreta:** entrar com a conta real em produção e registrar evidência de
`GET /api/article1/scientific-state -> HTTP 200`, confirmando na mesma sessão
`Doutorado — Willian Vagner -> Artigo 1 -> SCOPING_REVIEW -> D-132 -> Human Review -> Biblioteca`.

Depois disso, o closeout técnico pode ser marcado `PRODUCT CLOSED`; o próximo trabalho passa a ser
científico/humano: revisão de precisão, known items, validação provider-native e PRESS, sem abrir GF-10
antes das decisões correspondentes.
