# Revisão humana do vocabulário de busca

O vocabulário `config/query_vocabulary.json` transforma a pergunta escrita pela pessoa em blocos de busca (população, intervenção, desfecho etc.) com sinônimos em inglês e termos em português. Ele foi montado pela equipe e está como `curated_pending_human_review`: ainda falta a revisão de alguém com domínio de Medicina e Nutrição do Estilo de Vida.

Esta pasta prepara essa revisão:

| Arquivo | Para que serve |
| --- | --- |
| `query_vocabulary_review.csv` | Planilha com uma linha por conceito (113). Abra no Excel ou no Google Sheets. |
| `QUERY_VOCABULARY_PRE_REVIEW.md` | Verificações automáticas que apontam onde olhar primeiro. Elas não julgam significado. |

Os dois arquivos são gerados por `python tools/review_query_vocabulary.py` a partir do vocabulário. O teste `nutev_tests/test_query_vocabulary_review.py` falha se ficarem desatualizados.

## O que conferir em cada linha

| Coluna | Pergunta para o especialista |
| --- | --- |
| `label_pt` / `label_en` | O nome descreve o conceito? |
| `triggers` | São palavras que, numa pergunta, de fato indicam esse conceito? Alguma vai disparar o conceito errado? |
| `en_synonyms` | São os termos que um autor usaria em título ou resumo? Falta algum importante? Algum é amplo demais e traria artigos de outro assunto? |
| `pt_terms` | Servem para BVS/LILACS e SciELO? Falta algum termo usado na literatura brasileira? |
| `default_enabled` | O bloco deve entrar na busca por padrão, ou é amplo demais (como "adultos") e deve começar desligado? |
| `taxonomy_group` | O eixo MEV/NEV ligado ao conceito está certo? |
| `automatic_flags` | Avisos da pré-revisão: confirme ou descarte cada um. |

Não acrescente descritores MeSH/DeCS: o vocabulário só tem termos de texto livre, por decisão de projeto. No modo amplo, cada base aplica o próprio vocabulário controlado.

## Como registrar a decisão

Preencha `reviewer_decision` com `OK`, `ALTERAR` ou `REMOVER`. Em `reviewer_notes`, escreva o que mudar (por exemplo: "tirar 'diet' sozinho dos sinônimos" ou "acrescentar 'whole grain' em en_synonyms"). Comece pelos avisos de `QUERY_VOCABULARY_PRE_REVIEW.md`.

## Depois da revisão

As mudanças são aplicadas por quem mantém o código, num PR próprio:

1. Aplicar as alterações em `config/query_vocabulary.json`.
2. Subir `vocabulary_version` (por exemplo, `2026-11-v1`), porque o significado das buscas muda.
3. Só quando a planilha inteira tiver sido revisada: mudar `review_status` para `human_reviewed` e registrar quem revisou, a data e o SHA-256 da planilha preenchida. Atualizar o teste que hoje fixa o estado pendente.
4. Regenerar os artefatos: `python tools/review_query_vocabulary.py` e `python tools/build_open_explorer_data.py`.

Nenhum agente automatizado pode marcar o vocabulário como revisado por humano.
