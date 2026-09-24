# Jev × Humano × NutEV — validação comparativa

## Objetivo

Esta camada transforma o Semantic Shadow em um experimento mensurável, mantendo a fronteira
científica do NutEV.

Ela compara três fontes distintas sem fingir que medem exatamente a mesma coisa:

1. **Humano** — rótulos independentes de tipo documental e relevância nutricional;
2. **Jev** — descrição semântica probabilística produzida pelo shadow;
3. **NutEV** — `reference_score`, rank e tier como sinais de prioridade técnica de leitura.

O terceiro item é **exploratório**. O `reference_score` não vira ground truth, qualidade,
elegibilidade, certeza ou recomendação.

## Etapa 1 — preparar planilha de revisão humana

Depois de rodar o Semantic Shadow:

```bash
PYTHONPATH=src python tools/jev_compare_validation.py template \
  --ranking project_output_reference/reference_ranking/reference_ranking.jsonl \
  --shadow project_output_reference/jev_semantic_shadow/semantic_shadow.jsonl \
  --output project_output_reference/jev_semantic_shadow/HUMAN_LABELS.csv \
  --limit 100
```

O CSV já traz, para navegação do revisor:

- título;
- rank/score/tier do NutEV;
- tipo e score Jev.

O revisor preenche apenas:

- `human_document_type`;
- `human_nutrition_relevance` de 0 a 4;
- `reviewer_code` pseudônimo;
- `reviewed_at`;
- notas opcionais.

Rótulos humanos não são inclusão/exclusão e não viram PRISMA.

## Etapa 2 — analisar

```bash
PYTHONPATH=src python tools/jev_compare_validation.py analyze \
  --ranking project_output_reference/reference_ranking/reference_ranking.jsonl \
  --shadow project_output_reference/jev_semantic_shadow/semantic_shadow.jsonl \
  --human-labels project_output_reference/jev_semantic_shadow/HUMAN_LABELS.csv \
  --output-dir project_output_reference/jev_semantic_shadow/comparison
```

Saídas:

```text
JEV_COMPARISON_REPORT.json
JEV_COMPARISON_REPORT.md
```

## Métricas

### Jev vs humano — comparação direta

Tipo documental:

- acurácia exata;
- macro-F1;
- métricas por classe;
- Brier da confiança da escolha;
- ECE em 5 bins.

Relevância nutricional:

- MAE 0–4;
- proporção dentro de ±1 ponto;
- correlação de Spearman.

### NutEV vs humano — associação exploratória

- Spearman de `reference_score` vs relevância humana;
- Spearman da prioridade de rank vs relevância humana;
- média de relevância humana por tier.

### Jev vs NutEV — associação exploratória

- Spearman entre relevância Jev e `reference_score`.

Essas correlações não validam o score como qualidade científica.

## Guardrails

Todo relatório fixa:

```text
validation_claim = NOT_ESTABLISHED
ranking_effect = none
scientific_effect = none
```

O comparador:

- não escreve no ranking;
- não altera Semantic Shadow;
- não cria inclusão/exclusão;
- não cria estado PRISMA;
- não avalia risco de viés;
- não altera qualidade/certainty;
- não gera recomendação.

Uma eventual mudança desses estados deve continuar passando pelos contratos científicos e revisão
humana do NutEV.
