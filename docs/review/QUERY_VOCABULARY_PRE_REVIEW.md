# Pré-revisão automática do vocabulário de busca

> Arquivo gerado por `python tools/review_query_vocabulary.py`. Não editar à mão.

- Vocabulário: `2026-10-v1`, 113 conceitos.
- Estado: `curated_pending_human_review`. Esta pré-revisão **não** muda o estado; ela só aponta onde olhar.
- Achados: 1 avisos e 46 observações.

As verificações são mecânicas (gatilhos que se sobrepõem, sinônimos repetidos ou genéricos, siglas curtas, truncamento, falta de termos em português, conceitos sem eixo MEV/NEV). Elas não julgam significado. A planilha `query_vocabulary_review.csv` traz uma linha por conceito para a decisão do especialista; o procedimento está em `QUERY_VOCABULARY_REVIEW.md`.

## Contagem por tipo

| Código | Quantidade |
| --- | --- |
| `broad_single_word` | 1 |
| `no_taxonomy_axis` | 18 |
| `short_acronym` | 7 |
| `truncation` | 21 |

## Avisos (olhar primeiro)

| Conceito | Código | Detalhe |
| --- | --- | --- |
| `diet.healthy_eating` | `broad_single_word` | 'diet' alone matches far beyond this concept |
