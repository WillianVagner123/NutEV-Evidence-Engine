# Jev Semantic Shadow

## Escopo

O Jev Semantic Shadow é uma camada experimental e **separada** do ranking canônico do NutEV.

Ele serve para comparar descrições semânticas probabilísticas com o pipeline determinístico, sem
alterar:

- `reference_score`;
- `reference_rank`;
- faixas A/B/C;
- taxonomia canônica;
- quarentena/rastreabilidade;
- inclusão ou exclusão científica;
- PRISMA;
- risco de viés, qualidade ou certeza;
- recomendações clínicas/científicas.

O contrato é explícito em todo output:

```text
ranking_effect = none
scientific_effect = none
```

## Posição na arquitetura

O fluxo oficial permanece:

```text
SEARCH
  -> NORMALIZE
  -> TRACEABILITY GATE
  -> DEDUPLICATE
  -> CLASSIFY
  -> RANK
  -> EXPORT
  -> AUDIT
```

O shadow é uma derivação opcional posterior:

```text
canonical reference_ranking.jsonl (read-only)
                    |
                    +--> Jev Semantic Shadow
                           |
                           +--> semantic_shadow.jsonl
                           +--> JEV_SHADOW_MANIFEST.json
```

`tools/rank_references.py` não importa nem chama Jev.

## Estado enviado ao provider

Somente metadados bibliográficos minimizados:

- título;
- abstract/summary/snippet limitado a 4.000 caracteres;
- keywords/subjects limitados;
- tipo documental informado pelo provider;
- ano;
- provider.

Não são enviados:

- `reference_score`, rank/tier ou score breakdown;
- decisão humana de elegibilidade;
- decisão PRISMA;
- estado A1/A2;
- workspace/project/application IDs;
- full text/PDF;
- bindings ou owner pins;
- recomendações ou estados de síntese.

## Perguntas

Cada referência recebe três julgamentos independentes:

1. `document_type` — classificação documental;
2. `nutrition_relevance` — descrição semântica de 0–4;
3. `semantic_ambiguity` — probabilidade de metadata insuficiente/ambíguo.

Esses campos são **metadata experimental**. Eles não são evidência de validade científica.

## Execução

Por padrão o modo é `off`.

```bash
export NUTEV_JEV_MODE=shadow
export TYPESAFE_API_KEY='...'
export TYPESAFE_BASE_URL='https://api.typesafe.ai'
export TYPESAFE_DEFAULT_MODEL='jev-latest'
export NUTEV_JEV_TIMEOUT_SECONDS=3
export NUTEV_JEV_MAX_RECORDS=20

PYTHONPATH=src python tools/jev_semantic_shadow.py
```

Também é possível definir o limite explicitamente:

```bash
PYTHONPATH=src python tools/jev_semantic_shadow.py --mode shadow --limit 20
```

A chave é secret de runtime e nunca deve ser versionada.

## Saídas

```text
project_output_reference/jev_semantic_shadow/
  semantic_shadow.jsonl
  JEV_SHADOW_MANIFEST.json
```

O manifesto registra:

- SHA-256 do ranking canônico lido;
- modelo solicitado;
- número de registros disponíveis/selecionados;
- contagens de sucesso/falha;
- SHA-256 do output;
- assertions explícitas de ausência de efeito no ranking/estado científico.

Falhas de rede/provider são registradas por referência e não alteram o ranking canônico.

## Validação recomendada

Antes de qualquer hipótese de uso além de shadow, comparar contra classificação humana independente:

- acurácia/F1 por tipo documental;
- calibração das probabilidades;
- erro por provider e riqueza de metadata;
- estabilidade por idioma;
- divergência entre score lexical e descrição semântica;
- ganho ou ausência de ganho em workload.

Até essa validação existir, o shadow permanece experimental e não deve sustentar claims de
performance científica do NutEV.
