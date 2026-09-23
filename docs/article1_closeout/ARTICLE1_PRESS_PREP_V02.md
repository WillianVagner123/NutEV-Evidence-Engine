# Article 1 — PRESS Preparation v0.2

**Status:** `READY_FOR_HUMAN_PRESS_PREPARATION`, não `PRESS=PASS`.  
**Base:** Search Master canônico + query draft + PRESS worksheet + evidência D-132 persistida + snapshot DEVELOPMENT de 22/09.

## 1. Questão e tradução

A pergunta combina três objetos:

1. parâmetros nutricionais;
2. competências alimentares;
3. contextos sociais da alimentação;

aplicados às funções:

- avaliar;
- aconselhar;
- prescrever;
- monitorar.

Arquitetura atual:

- B-NORM = fontes normativas;
- C1 = care process;
- C2 = competency/literacy;
- C3 = implementation;
- C4 = social context, ainda candidato PRESS.

“Parâmetros nutricionais” não possui subrota dedicada; essa é uma decisão metodológica aberta.

## 2. B-NORM

Estrutura canônica:

`nutrition_anchor AND normative_marker`.

No snapshot DEVELOPMENT de 22/09:

- B-NORM = 139.460;
- `standard*` exclusivo ≈ 68.735 (49,29%);
- `recommendation*` exclusivo ≈ 22.639;
- `guideline*` exclusivo ≈ 19.236;
- `guidance` exclusivo ≈ 5.489;
- `consensus` exclusivo ≈ 3.634.

Interpretação permitida: `standard*` merece avaliação de precisão por potencial uso genérico (“standard deviation”, “standardized”, etc.).

Não permitido: concluir automaticamente que `standard*` deve ser removido.

Alternativa DEVELOPMENT descrita no handoff:

- BN-ALT-ti ≈ 11.884 registros;
- ≈ 8,5% do tamanho da rota atual;
- recuperou 5/5 known items normativos usados naquele teste;
- caveat: os known items utilizados favoreciam títulos com marcador normativo.

Decisão depende de revisão humana S1/S2/S3 ou protocolo equivalente materializado.

## 3. C1 — CARE PROCESS

Snapshot DEVELOPMENT:

- baseline ≈ 4.073;
- dietary/diet/nutritional counsel(l)ing: +2.986 (+73,3%);
- `meal plan*`: +536;
- etapas NCP: +138;
- `nutrition care`: +1.191;
- `nutrition intervention*`: +4.482;
- nutrition/nutritional therapy: +4.953.

Pergunta PRESS: o incremento representa estruturas operacionais de cuidado ou counseling/therapy genéricos demais?

## 4. C2 — COMPETENCY/LITERACY

Snapshot DEVELOPMENT:

- baseline ≈ 1.772;
- `eating competence` + âncora eating: +115 e recupera KI03;
- culinary/cooking skill variants: +93;
- physician/LM competenc*: +12 e recupera KI08;
- `meal planning`: +367;
- `health literacy`: +1.207;
- `nutrition knowledge`: +2.132.

Construtos a manter separados:

- food literacy;
- nutrition literacy;
- food skills;
- culinary skills;
- food agency;
- eating competence;
- professional competence.

## 5. C3 — IMPLEMENTATION

Snapshot DEVELOPMENT:

- baseline ≈ 1.868;
- knowledge translation +193;
- RE-AIM/CFIR +301;
- implementation science +344;
- quality improvement +1.831;
- `implementation` solto +17.059 (+913%).

O último é sonda de ruído, não candidato aprovado.

## 6. C4 — SOCIAL CONTEXT

C4 permanece `PRESS_ONLY_CANDIDATE_NOT_APPROVED`.

Snapshot DEVELOPMENT:

- C4 isolada ≈ 7.615;
- C1–C3 union ≈ 7.573;
- C1–C4 union ≈ 14.959;
- incremento de C4 ≈ 7.386.

Isso justifica revisão humana de precisão; não justifica adoção automática.

Conceitos a separar:

- food environment;
- social determinants;
- social support;
- commensality/eating together;
- family meals;
- food culture;
- food insecurity;
- policy/monitoring.

## 7. Known items

Known items são sentinelas de desenvolvimento. Recuperar um known item é evidência diagnóstica da query, não validação suficiente.

Gaps prioritários:

- KI03 — eating competence;
- KI08 — professional competencies em Lifestyle Medicine;
- KI10 — food environments;
- KI13 — Lifestyle Medicine / Healthy Nutrition sem recuperação nas variantes descritas.

## 8. Delta tests canônicos

O PRESS worksheet canônico exige:

- D01 — B-NORM baseline vs + `food based`;
- D02 — B-NORM baseline vs + `healthy eating`;
- D03 — C1 com vs sem `meal plan*`;
- D04 — C3 standalone yield + manual precision sample;
- D05 — C4 incremental yield + manual precision sample.

A execução técnica persistida de 06/09 permanece humana-pendente.

## 9. Revisão humana de precisão

### D-132 v1

Existe e é canônico, mas tem limitação de recência para inferência global.

### S1–S6

O desenho DEVELOPMENT de 22/09 é metodologicamente útil para as questões novas, mas seus arquivos não estão materializados. Antes de qualquer julgamento:

1. versionar protocolo;
2. regenerar frames;
3. registrar denominadores;
4. gerar amostra determinística/estratificada;
5. gerar manifesto e hashes;
6. produzir dois packets cegos;
7. só então revisar Y/N/U.

## 10. Provider-native validation

Pendente:

- PubMed;
- LILACS/BVS;
- SciELO;
- Scopus;
- Web of Science.

Scopus/WoS não podem ser simulados como se tivessem sido validados.

## 11. Estado de fechamento PRESS

```text
P01–P10 = PENDING
PRESS DECISION = null
C4 DECISION = PENDING_HUMAN_DECISION
GF-10 = false
QUERY FREEZE = false
FORMAL SEARCH = false
PRISMA = false
```

## 12. Para PRESS humano

Antes de uma decisão PASS/REVISE:

- revisar precisão das áreas críticas;
- revisar known items;
- validar sintaxe de cada provider;
- decidir C4;
- decidir escopo de parâmetros nutricionais;
- documentar tradução entre bases;
- registrar revisor e data no record canônico.
