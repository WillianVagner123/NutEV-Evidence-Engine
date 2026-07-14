# Codificação dos domínios analíticos A/B/C/D (Artigo 1)

A classificação de cada documento nos quatro domínios analíticos **é o achado
central** do Artigo 1. Este documento define a regra de codificação, que é
implementada em `nutev.analysis.article1_coding` e reportada na **Matriz de
Integração** (`06_tables/NUTEV_DOMAIN_INTEGRATION_MATRIX.csv`).

## Os quatro domínios

| Domínio | Definição |
|--------|-----------|
| **A** | Composição e qualidade da dieta (nutrientes, grupos alimentares, padrões alimentares, ultraprocessados…) |
| **B** | Literacia alimentar, competências culinárias, planejamento (habilidade de cozinhar, leitura de rótulo, planejamento de refeições…) |
| **C** | Comensalidade, cultura, contexto das refeições (refeição em família, cultura alimentar, ambiente da refeição…) |
| **D** | Adesão, viabilidade, barreiras, facilitadores, implementação |

## A regra substantiva (o ponto crítico)

Um domínio só é marcado como `True` quando é contemplado de forma
**substantiva** — o documento traz **recomendação, orientação ou conteúdo
acionável** naquele domínio. **Menção retórica não conta.**

- ❌ "é importante cozinhar em casa" (menção retórica) → **não** marca B.
- ✅ "recomenda-se ensinar habilidades culinárias por meio de oficinas de preparo"
  (conteúdo acionável) → marca B.

Operacionalmente (`code_domains`), um domínio conta quando:

1. há **pelo menos uma** palavra-chave do domínio no texto (título + resumo +
   texto extraído); **e**
2. o contexto é **substantivo**: existe uma pista acionável no texto (recomenda,
   deve, diretriz, estratégia, intervenção, *recommend*, *should*, *guidance*,
   *strategy*, *intervention*…) em texto de tamanho suficiente, **ou** o próprio
   documento é um guia/diretriz/consenso (cujo propósito é orientar).

Campos derivados: `profile` (ex.: `"AD"`, `"ABCD"`), `n_domains` (0–4).

## Marcadores de contexto (argumento brasileiro)

- `mentions_cost` — o documento aborda custo/acessibilidade econômica.
- `mentions_equity` — o documento aborda equidade/iniquidade/vulnerabilidade.
- Cruzamento reportado: "menciona custo **E** oferece estratégia" (custo + domínio
  D substantivo).

## Codificação assistida, decisão humana

A codificação do sistema é **assistiva**, nunca final. Todo documento entra na
fila de revisão humana com `domain_coding_needs_human_review = True`. O revisor
confirma ou corrige, e a decisão é registrada em
`07_logs/human_review_decisions.csv` com: sugestão do sistema, decisão humana e
concordância — o que permite calcular a **concordância (kappa)** depois. Ver
`nutev.review` e [`docs/SCIENTIFIC_GOVERNANCE.md`](SCIENTIFIC_GOVERNANCE.md).

## Limitações declaradas

A codificação automática é **heurística baseada em léxico** — é um ponto de
partida auditável, não um classificador validado. O léxico (em português e
inglês) está explícito no código para inspeção e ajuste. A validade do achado
depende da **revisão humana** de cada documento; a concordância humano×sistema
deve ser reportada no artigo.
