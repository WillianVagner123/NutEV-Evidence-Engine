# Article 1 — Current State

**Natureza:** documento de trabalho de fechamento.  
**Autoridade científica:** `ARTICLE1_SEARCH_MASTER.md` + `config/nutev/article1_search_master_v1.json`.  
**Autoridade de runtime mutável:** manifests/runtime do NutEV quando materializados.  
**Não é:** PRISMA, decisão de elegibilidade, PRESS PASS ou freeze.

## Pergunta

> Quais parâmetros nutricionais, competências alimentares e contextos sociais da alimentação são atualmente recomendados, estruturados e utilizados por diretrizes e modelos operacionais para orientar avaliação, aconselhamento, prescrição e monitoramento alimentar aplicáveis à Medicina do Estilo de Vida?

## Gates canônicos

| Gate | Estado |
|---|---|
| Discovery | concluído |
| PRESS | pendente; `NOT_YET_RECORDED_AS_PASS` |
| GF-10 | não autorizado |
| Query freeze | pendente |
| Formal provider search | não executada |
| Formal PRISMA search event | não criado |
| C4 | `PRESS_ONLY_CANDIDATE_NOT_APPROVED` |

Nenhuma ação de fechamento técnico autoriza alteração desses estados.

## Produto / tenancy

Estado operacional materializado:

- workspace: `Doutorado — Willian Vagner`;
- projeto: `Artigo 1`;
- aplicação: `SCOPING_REVIEW`;
- owner: Willian Vagner / `WORKSPACE_OWNER`;
- `assembly_id=WILLIAN_DOCTORATE_A1`;
- `d132_config_version=d132-v1`;
- owner pins A1 configurados e validados no processo de produção;
- configuração protegida de persistência dos owner pins em `/etc/nutev/article1-owner.env`;
- PR de deploy com sincronização fail-closed dos pins: #1310;
- browser context-selection flake corrigido por #1311.

O SHA final de produção deve ser estampado no `ARTICLE1_CLOSEOUT_REPORT.md` somente após a promoção exact-SHA e prova do runtime.

## Snapshot científico estático de 2026-08-30

Search id: `web_20260830T182743+0000_91bde5be`.

| Medida | Valor |
|---|---:|
| Registros antes da deduplicação | 41.139 |
| Referências únicas | 33.839 |
| Aceitos estruturalmente | 33.067 |
| Quarentena estrutural | 772 |
| Tier A | 662 |
| Retrieved | 504 |
| Partial | 90 |
| Not retrieved | 68 |
| Retrieved + partial | 594 / 662 = 89,73% |
| B-NORM | 85 |
| C-STRUCT | 316 |
| União | 351 |
| Overlap | 50 |
| Unrouted | 311 |
| Vocabulary audit B-NORM | 27 candidatos |
| Vocabulary audit C-STRUCT | 49 candidatos |

Essas contagens são de discovery/deepening/navegação. Não são screening, inclusão, exclusão ou PRISMA.

## D-132 canônico

Fonte persistida no repositório:

`evidence/article1_press/article1_press_20260906T202201Z/`

Contrato:

- `d132-v1`;
- `D-132`;
- `MANIFEST_EXACT`;
- 100 registros;
- D02 = 25;
- D03 = 25;
- D04 = 25;
- D05 = 25;
- dois revisores por item;
- slots A/B;
- Y/N/U;
- razão obrigatória;
- adjudicação humana;
- nenhuma alteração automática de PRESS, C4, GF-10, freeze, busca formal ou PRISMA.

Limitação conhecida: o conjunto canônico D02–D05 deriva da amostragem técnica por `rows[:limit]`; no handoff DEVELOPMENT de 22/09 foi observado forte viés de recência. Portanto D-132 v1 não deve ser tratado como estimativa global de precisão sem decisão metodológica humana.

## Pacote S1–S6

O handoff de 22/09 descreveu um pacote novo de 150 registros, 25 por fatia:

- S1: B-NORM exclusivo por `standard*`;
- S2: B-NORM exclusivo por `recommendation*`;
- S3: registros perdidos por BN-ALT-ti;
- S4: incremento de counsel(l)ing em C1;
- S5: incremento exclusivo de C4 sobre C1–C3;
- S6: incremento de `eating competence`.

Auditoria de runtime posterior confirmou que os arquivos desse pacote **não foram materializados no servidor/volume atual**. Portanto:

```text
S1–S6 STATUS = PROTOCOL/SNAPSHOT DESCRIBED, FILES NOT CANONICALLY MATERIALIZED
```

Não reconstruir linhas/PMIDs por inferência. Se o desenho for mantido, regenerar de modo determinístico e versionado.

## Próximo gate real

O próximo gate científico é completar evidência pré-PRESS com revisão humana e validação por provider. O produto pode ser tecnicamente fechado antes disso; o Artigo 1 não pode ser declarado pronto para busca formal antes de decisão humana de PRESS e autorização GF-10.
