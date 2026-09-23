# Article 1 — Query Delta Plan

**Natureza:** plano pré-freeze. Nenhuma execução descrita aqui é automaticamente FORMAL.

## A. Deltas canônicos do PRESS worksheet

| ID | Rota | Comparação | Estado científico |
|---|---|---|---|
| D01 | B-NORM | baseline vs + `food based` | revisão humana pendente |
| D02 | B-NORM | baseline vs + `healthy eating` | revisão humana pendente |
| D03 | C1 | com vs sem `meal plan*` | revisão humana pendente |
| D04 | C3 | standalone yield + precision | revisão humana pendente |
| D05 | C4 | incremento fora das demais rotas | revisão humana pendente |

A execução técnica de 06/09 tem fonte persistida e 100 registros D02–D05 no D-132.

## B. Exploração adicional de 22/09

O handoff descreveu 119 consultas DEVELOPMENT + verificações extras. Esses números não foram adotados no worksheet canônico e não são formal search.

Pontos que merecem teste/revisão adicional:

### B-NORM

- precisão de `standard*`;
- precisão de `recommendation*`;
- perdas de uma alternativa title-restricted (BN-ALT-ti);
- controlled vocabulary/publication types;
- impacto de anchors `nutrition*`, `food`, MeSH.

### C1

- counsel(l)ing;
- NCP stages;
- nutrition care/intervention/therapy;
- meal plan.

### C2

- eating competence;
- culinary/cooking skills;
- physician/Lifestyle Medicine competence;
- meal planning;
- health literacy;
- nutrition knowledge.

### C3

- knowledge translation;
- RE-AIM/CFIR;
- implementation science;
- quality improvement;
- não usar `implementation` solto como candidato sem revisão.

### C4

- eating together/family mealtime;
- food culture;
- policy/monitoring;
- ausência de marcador operacional;
- food (in)security;
- marcador operacional estreito.

## C. Protocolo para novos deltas

Para qualquer candidato:

1. fixar query baseline;
2. fixar variant query;
3. construir `variant NOT baseline`;
4. registrar provider e sintaxe;
5. registrar timestamp;
6. registrar contagem baseline/variant/incremental;
7. registrar known-item recovery;
8. materializar frame ou estratégia de amostragem;
9. criar sample manifest com hashes;
10. revisão humana;
11. não atualizar PRESS automaticamente.

## D. S1–S6 — desenho a regenerar

O desenho descrito em 22/09:

| Slice | Pergunta |
|---|---|
| S1 | qual a precisão do B-NORM exclusivo por `standard*`? |
| S2 | qual a precisão do B-NORM exclusivo por `recommendation*`? |
| S3 | que material relevante BN-ALT-ti perderia? |
| S4 | qual a precisão do incremento de counsel(l)ing em C1? |
| S5 | qual a precisão do incremento exclusivo de C4? |
| S6 | qual a precisão do incremento de eating competence? |

Arquivos antigos não estão materializados. Regeneração obrigatória se esse desenho for aprovado.

Parâmetros descritos no handoff que devem ser preservados se a regeneração for escolhida:

- 25 registros por slice;
- randomização pseudoaleatória reprodutível;
- seed original descrita: 20260922;
- S3 deve relatar cobertura do frame (o snapshot local reportou 87,2%);
- nenhuma informação de rank/score/machine relevance nos packets cegos.

## E. Critério de parada

Parar testes exploratórios quando houver evidência suficiente para o revisor humano julgar:

- sensibilidade aparente;
- precisão manual;
- known-item recovery;
- ruído;
- fidelidade de tradução por provider.

Não otimizar indefinidamente antes de PRESS.
