# Article 1 — Writing State

**Natureza:** controle editorial do manuscrito. **Não** é fonte de verdade científica.
Estado científico: `ARTICLE1_SEARCH_MASTER.md` + `config/nutev/article1_search_master_v1.json` + `config/nutev/article1_press_review_v1.json`.
Protocolo/codebook: documento canônico do Drive "A1 — PROTOCOLO OPERACIONAL E CODEBOOK ABCD-NUT-EV — VERSÃO CANÔNICA" (v1.2-candidata).

## PRODUCT STATUS

```text
ARTICLE1_PRODUCT_STATUS   = CLOSED
OWNER ACCEPTANCE          = PASS (2026-09-28T13:30Z, registrada em #1327)
PRODUCTION_SHA            = a3034e6992ec2061d316aae5e23b9410e23d5c9b
GET /api/article1/scientific-state = HTTP 200
```

## SCIENTIFIC STATE

```text
status                        = DISCOVERY_CLOSED_FORMAL_SEARCH_PENDING_PRESS_FREEZE
press_status                  = NOT_YET_RECORDED_AS_PASS
gf10_authorized               = false
query_freeze_complete         = false
formal_provider_search_executed = false
prisma_search_event_emitted   = false
ARTICLE1_SCIENTIFIC_READY     = false
```

## CANONICAL MANUSCRIPT

```text
title       : A1 — MANUSCRITO CANÔNICO — RECOMENDAÇÕES E DIREÇÃO ALIMENTAR
google_doc  : 1--D7m5YG3LaxZSBxXm2AW4HqLz_WGN51Qhb1U9IQBXI
edit mode   : Sugestões (todas as alterações desta sessão são sugestões pendentes de aceite humano)
comments    : nenhum comentário existente no documento em 2026-09-28
LAST REVIEWED AT  : 2026-09-28 (leitura integral do texto exportado)
LAST REVIEWED SHA : a3034e6992ec2061d316aae5e23b9410e23d5c9b
references  : 29/29 DOIs resolvidos no Crossref; 1º autor, periódico e volume conferidos
```

## SECTIONS

| Seção | Estado | Observação |
|---|---|---|
| TITLE | READY_FOR_HUMAN_REVIEW | Título PT/EN alinhado à pergunta canônica aprovada em 2026-09-28 e aplicado no manuscrito. |
| INTRODUCTION | READY_FOR_HUMAN_REVIEW | Já contém problema, lacuna, literatura, distinção recomendação × execução e justificativa. Referências verificadas. Nenhuma frase nova com citação foi adicionada. |
| OBJECTIVE | READY_FOR_HUMAN_REVIEW | Objetivo geral alinhado à pergunta canônica aprovada e aplicado no manuscrito/protocolo; objetivos específicos permanecem os do protocolo v1.2-candidata. |
| METHODS | DRAFT | Sugeridos 2.5.1 (descoberta, arquitetura de rotas, testes delta, sentinelas, PRESS, tradução nativa, freeze) e parágrafo em 2.11 (citação do software, identidade determinística, ranking ≠ elegibilidade, limites do Engine). |
| RESULTS | BLOCKED_BY_FORMAL_SEARCH | Sugerida 3.1.1 com estrutura R1–R7 marcada `PENDING_FORMAL_EXECUTION` (R8–R10 ainda não inseridos no Doc); nenhum número inserido. |
| DISCUSSION | BLOCKED_BY_FORMAL_SEARCH | Esqueleto prospectivo já existe (4.1–4.9) e está explicitamente formulado como hipótese. Comparação com a literatura depende dos resultados. |
| CONCLUSION | BLOCKED_BY_FORMAL_SEARCH | Seção 5 é conclusão da etapa pré-execução, sem achados. Manter assim. |
| TABLES | NOT_STARTED | T1 características; T2 ABCD × família; T3 exclusões em texto completo — todas dependem do corpus formal. |
| FIGURES | NOT_STARTED | F1 PRISMA-ScR; F2 marcadores M1–M10; F3 coocorrência; F4 relações explícitas — dependem do corpus formal. |
| SUPPLEMENTS | DRAFT | Strings candidatas (ver `ARTICLE1_PRESS_PACKET_V01.md`), codebook (Drive), auditoria de desenvolvimento (discovery) — não finalizados. |

## TITLE AUDIT

Título canônico alinhado à decisão de 2026-09-28:

- PT: *Da recomendação à execução: como documentos normativos e estruturantes do cuidado alimentar de adultos operacionalizam a direção dietética — revisão de escopo com análise documental*
- EN: *From recommendation to execution: how normative and structuring documents for adult dietary care operationalize dietary direction — a scoping review with documentary analysis*

Aplicado no manuscrito canônico. A formulação anterior do Search Master fica preservada apenas em histórico/versionamento.

## SOURCE DRIFT (registrada, não resolvida)

| # | Tema | Manuscrito | Protocolo v1.2-candidata (Drive) | Engine (repo) |
|---|---|---|---|---|
| 1 | Pergunta | **RESOLVIDA 2026-09-28** — mesma pergunta canônica aprovada | **RESOLVIDA 2026-09-28** — mesma pergunta canônica aprovada | **RESOLVIDA 2026-09-28** — Search Master sincronizado |
| 2 | Bases formais | PubMed, Scopus, WoS | PubMed, Scopus, WoS | PubMed, LILACS/BVS, SciELO, Scopus, WoS |
| 3 | Estratégias | "normativa" + "estruturante" | B-NORM-PUBMED v0.4, C-STRUCT-PUBMED v0.3 | B-NORM + C1–C4 (C4 PRESS-only); base operacional cita B v0.7 / C v0.5.1 (D-129–D-131) |
| 4 | Sentinelas | 16 | 16 (implícito) | 14 known items (KI01–KI14) |
| 5 | Rótulo D-132 | — | — | amostra de precisão dos testes delta (100 registros); na base operacional D-132 é a proposta de modelo de revisores |

O comentário "A1 authority clarification" em #1327 definiu o Engine como autoridade de **execução da busca** e o Drive D-124–D-132 como proveniência. A divergência da **pergunta** foi resolvida em 2026-09-28 por Willian/Dr. Caio; lista de bases, estratégia final e demais gates continuam decisões separadas.

## A1 SCIENTIFIC GATE MATRIX (2026-09-28)

| Gate | Estado | Evidência |
|---|---|---|
| PRESS | PENDING | `article1_press_review_v1.json`: status DRAFT, reviewer null, P01–P10 PENDING |
| R1 | HUMAN_DECISION_REQUIRED | nenhum revisor designado no repo ou no protocolo |
| R2 | HUMAN_DECISION_REQUIRED | idem; protocolo exige designação real antes de qualquer concordância |
| ADJUDICATOR | HUMAN_DECISION_REQUIRED | idem |
| PRESS REVIEWER | ASSIGNED_PENDING_REVIEW | Vagner — UnB; ainda faltam data, declaração explícita de independência e parecer P01–P10 do próprio revisor |
| PUBMED NATIVE VALIDATION | PENDING | auditoria oficial de sintaxe v0.2 concluída: wildcard em frases é suportado; ainda faltam Search Details nativo, balanço MeSH/free-text e testes de resgate controlado |
| LILACS/BVS NATIVE VALIDATION | BLOCKED | interface pública HTTP 403 nas tentativas técnicas (D-130); também depende de decisão de incluir a base |
| SCIELO NATIVE VALIDATION | BLOCKED | idem |
| SCOPUS NATIVE VALIDATION | EXTERNAL_VALIDATION_REQUIRED | acesso licenciado; simulação proibida |
| WEB OF SCIENCE NATIVE VALIDATION | EXTERNAL_VALIDATION_REQUIRED | acesso licenciado; simulação proibida |
| GF-01 | PENDING | base operacional: PARTIAL (rota regional técnica não resolvida) — relatado em #1327 |
| GF-02 | PENDING | reaberto condicionalmente pelo micro-PILOT de sintaxe (D-131) — relatado em #1327 |
| GF-03 | PENDING | bloqueador ativo na base operacional — relatado em #1327 |
| GF-07 | HUMAN_DECISION_REQUIRED | modelo de revisores (proposta "D-132" do Drive) aguarda aprovação do orientador |
| GF-10 | PENDING | `gf10_authorized=false`; requer PRESS PASS + deltas + decisão C4 + validação nativa |
| QUERY FREEZE | PENDING | `query_freeze_complete=false` |
| PROTOCOL FREEZE | PENDING | protocolo v1.2-candidata; OSF não submetido |
| FORMAL SEARCH AUTHORIZATION | BLOCKED | bloqueado por PRESS, GF-10 e freeze |

GF-01/02/03 foram classificados a partir dos comentários de reconciliação em #1327 (base operacional do Drive), não de leitura direta dessa planilha nesta sessão.

## SCIENTIFIC BLOCKERS

1. PRESS reviewer designado (Vagner — UnB), mas o parecer ainda exige data, declaração de independência, P01–P10 e decisão final do próprio revisor. R1, R2 e adjudicador continuam não designados.
2. PubMed teve auditoria oficial de sintaxe, mas ainda requer Search Details nativo e deltas controlados; LILACS/BVS e SciELO seguem tecnicamente bloqueados; Scopus/WoS exigem acesso licenciado.
3. Versão final das estratégias e decisão sobre C4 ainda dependem de PRESS/delta review.

## HUMAN DECISIONS REQUIRED

1. Lista final de bases formais (incluir ou não LILACS/BVS e SciELO).
2. Versões de estratégia a submeter ao PRESS (B-NORM + C1–C4 do Engine vs B v0.7 / C v0.5.1 da base operacional).
3. Designar R1, R2 e adjudicador; para PRESS, Vagner — UnB já foi designado, faltando o parecer independente propriamente dito.
4. Decisão sobre C4 (ADOPT/REVISE/REJECT) após revisão das amostras.
5. D-132 v1 exploratório vs D-132b aleatório/estratificado; renomear um dos dois "D-132".
6. Harmonizar sentinelas (16 vs 14).
7. Aceitar/rejeitar/reconciliar as demais sugestões editoriais do Google Doc.

## NEXT WRITING ACTION

Pergunta/título/objetivo já harmonizados. Auditoria técnica PubMed v0.2 preparada em `ARTICLE1_PRESS_TECHNICAL_AUDIT_V02.md`; próxima ação é executar Search Details/deltas controlados e entregar o pacote a um revisor PRESS independente antes de qualquer freeze.
