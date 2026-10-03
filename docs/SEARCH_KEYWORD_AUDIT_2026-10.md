# Auditoria interna — palavras-chave e construção de buscas (2026-10)

**Pergunta auditada:** como o NutEV transforma o que a pessoa escreve em buscas nas bases, e o que falta para que alguém digite uma pergunta (como em grandes portais) e o sistema organize os conceitos, monte a string de cada base no formato dela e dispare a busca.

**Escopo:** busca hospedada (`apps/nutev-web`), compiladores de consulta (`apps/nutev-web/query_compiler.py`, `src/nutev/science/article1_press.py`, `src/nutev/science/topic_audit.py`), coleta do Engine (`config/reference_search.json`, `tools/run_everything_now.py`, `tools/run_latin_sources.py`), vocabulários (`config/keyword_taxonomy*.json`, `config/taxonomy_registry.json`, configurações do Artigo 1) e o Explorador Aberto (`apps/nutev-open`).

**Natureza:** auditoria técnica de software. Não altera estado científico, PRESS, GF-10, congelamento de consulta, busca formal ou PRISMA.

## 1. Como era antes desta entrega

| # | Achado | Evidência | Efeito |
| --- | --- | --- | --- |
| A1 | A "busca rápida" envia a pergunta crua, sem interpretação, a todas as bases. | `query_compiler.compile_query_plan` modo `natural_language_passthrough`; teste `test_review_query_compiler.py`. | Pergunta em português chega a PubMed, OpenAlex e Crossref, que indexam majoritariamente em inglês; palavras como "melhora", "efeito" e "em adultos" viram termos obrigatórios. |
| A2 | Não existia extração de conceitos, sinônimos, tradução PT↔EN nem mapeamento para PICO/PCC a partir de texto livre. | `search-guided-recovery.js:35` e `:73` ("não expande termos científicos automaticamente"). | O usuário precisa escrever cada termo à mão no modo avançado (`free:`, `mesh:`, `decs:`). |
| A3 | O vocabulário existente (taxonomia canônica, 58 eixos, 1.196 termos PT/EN) só era usado para classificar e ordenar, nunca para montar buscas. | `src/nutev/taxonomy.py`, `tools/rank_references.py`. | O conhecimento de MEV/NEV já curado não ajudava a pessoa a buscar. |
| A4 | Termos DeCS em português viram texto livre `[Title/Abstract]` no PubMed, e um teste fixa esse comportamento. | `test_review_query_compiler.py:42` (`"Medicina do Estilo de Vida"[Title/Abstract]`). | Termos em português enviados a uma base em inglês quase não recuperam nada. |
| A5 | Truncamento é perdido em um dos compiladores. | `topic_audit._quote_term` remove `*` (`src/nutev/science/topic_audit.py:452-455`). | `diet*` vira `diet`, reduzindo recall. |
| A6 | Não há tradução de sintaxe por base para truncamento regional. | BVS/SciELO usam `$`; nenhum compilador converte. | Strings com `*` não truncam nessas bases. |
| A7 | SciELO é chamado sempre com `lang=en` e envolvido em `subject:(...)`; LILACS/SciELO retornam só títulos da primeira página. | `tools/run_latin_sources.py:83-87`. | Recuperação regional limitada e pouco rastreável. |
| A8 | No caminho web, falha de conector legado pode aparecer como "vazio" em vez de "falhou". | `apps/nutev-web/search_adapter.py:105` (`"completed" if rows else "empty"`). | Ausência de resultados pode ser confundida com ausência de literatura. |
| A9 | "Search details" do PubMed (`querytranslation`, avisos) só são guardados nos modos de revisão. | `apps/nutev-web/progress_search.py:112`. | Na busca rápida a pessoa não vê como o PubMed interpretou a consulta. |
| A10 | O histórico só restaura a pergunta em modo rápido; estratégias avançadas e exatas se perdem. | `apps/nutev-web/search-history-ui.js:43-49`. | Retomar uma busca exige redigitar a estratégia. |
| A11 | Classificação e ordenação usam correspondência por substring. | `tools/rank_references.py:335-341` (`term in title`). | Falsos positivos possíveis (`iron` ⊂ `environment`, `fat` ⊂ `fatigue`). Não afeta a montagem de buscas, mas afeta a leitura dos eixos. |
| A12 | Crossref recebe `query=` e ignora booleanos; filtros de data e tipo nunca são passados. | `src/nutev/search/crossref.py:124`, `openalex.py:103`. | Período pedido pela pessoa não chega às bases. |

O que já estava bom e foi preservado: o modo exato versionado (`strategy_id`/`strategy_version`), a recusa em inventar MeSH/DeCS, os dialetos explícitos `pubmed_mesh_title_abstract`, `europepmc_mesh_title_abstract` e `bvs_decs_mesh_tw` e o aviso de sintaxe sem reescrita silenciosa.

## 2. O que esta entrega acrescenta

### 2.1 Vocabulário de busca curado — `config/query_vocabulary.json`

- 113 conceitos de MEV/NEV (dietas e padrões, pilares da MEV, comportamento e cuidado, acesso a alimentos, contexto, condições, desfechos, tipos de estudo), cada um com:
  - **gatilhos** em português e inglês para reconhecer o conceito na pergunta;
  - **sinônimos em inglês** (texto livre, com truncamento só em palavras únicas);
  - **termos em português** para BVS/LILACS e SciELO;
  - **papel PICO** (população/condição, intervenção/exposição, contexto, desfecho, tipo de estudo);
  - vínculo opcional com o **eixo canônico** da taxonomia MEV/NEV;
  - para tipos de estudo, **filtros do PubMed** (`systematic[sb]`, `meta-analysis[pt]`, `randomized controlled trial[pt]`, `guideline[pt]`, `practice guideline[pt]`).
- **Sem MeSH/DeCS inventados.** O arquivo não contém cabeçalhos controlados. No modo "Ampla", é a própria base que aplica o vocabulário dela: mapeamento automático do PubMed e sinônimos MeSH do Europe PMC (`synonym=true`). A interpretação devolvida pelo PubMed é mostrada à pessoa.
- Validação fail-closed: ids únicos, gatilhos sem ambiguidade entre conceitos, eixos existentes na taxonomia, termos sem aspas e truncamento só em palavra única.
- Estado: `review_status = curated_pending_human_review`. Precisa de revisão humana de especialista antes de servir a uma busca formal.

### 2.2 Planejador determinístico — `src/nutev/search/question_planner.py`

```text
pergunta (PT ou EN)
  -> normalização (acentos, caixa, pontuação)
  -> períodos ("desde 2015", "entre 2010 e 2020", "nos últimos 5 anos", "before 2010")
  -> marcadores de comparação ("versus", "comparado com") -> bloco Comparador (desligado por padrão)
  -> conceitos do vocabulário (correspondência mais longa primeiro, plural simples)
  -> palavras restantes sem valor de busca descartadas e listadas; demais viram "termo livre"
  -> blocos: sinônimos unidos por OR, blocos unidos por AND
     (desfechos e tipos de estudo agrupados; conceitos irmãos fundidos: obesidade/sobrepeso,
      crianças/adolescentes, diabetes/pré-diabetes...)
  -> uma string por base, no formato da base
```

| Base | Formato gerado | Período |
| --- | --- | --- |
| PubMed | `"termo"[tiab]`, truncamento `palavra*[tiab]`, filtros `[pt]`/`[sb]`, `sort=relevance`; no modo amplo, termos livres para o mapeamento automático | `AAAA:AAAA[dp]` |
| Europe PMC | `TITLE_ABS:"termo"`; no modo amplo, todos os campos + `synonym=true` | `PUB_YEAR:[AAAA TO AAAA]` |
| OpenAlex | booleana com frases entre aspas, sem `*` (a base faz radicalização própria) | `filter=from_/to_publication_date` |
| Crossref | palavras-chave por relevância (a base não aceita booleanos), via `query.bibliographic`: os dois primeiros termos em inglês de cada bloco e os sinônimos acrescentados, até 14 palavras | `filter=from-/until-pub-date` |
| BVS/LILACS | cada bloco dentro do campo `tw` (título, resumo e assunto): `tw:("termo" OR ...) AND tw:(...)`, em português e inglês, truncamento `$`; link com filtro LILACS. Verificado no portal em 2026-10-03: `tw:"termo"` em cada termo e a string sem campo deram 0; um grupo sem campo devolveu a coleção inteira; `tw:(...)` por bloco deu 15 no LILACS e 468 na coleção completa | aplicado no site |
| SciELO | booleana em português e inglês, truncamento `$` | aplicado no site |

Palavras fora do vocabulário viram um bloco livre cada uma, combinadas com AND (como numa busca por palavras-chave), e não uma frase exata.

Uma string já escrita com operadores, aspas ou campos (`AND`, `"..."`, `[tiab]`, `TITLE_ABS:`, `tw:`) é tratada como **string avançada** e enviada literalmente; a pessoa pode pedir "interpretar como pergunta". Se ela usa campos do PubMed (`[tiab]`, `[mh]`), a interface avisa que as outras bases recebem o mesmo texto.

`to_review_strategy(plan)` projeta o plano no esquema `free:` do modo avançado hospedado. Um teste prova que `apps/nutev-web/query_compiler.py` aceita essa saída sem gerar termos controlados.

### 2.3 Onde a pessoa usa

- **Explorador Aberto** (`apps/nutev-open`): a pessoa escreve a pergunta e a busca dispara direto. O painel "Como o NutEV organizou sua busca" mostra os blocos, de onde cada um foi reconhecido e o eixo MEV/NEV. Nele dá para ligar e desligar blocos e termos, acrescentar sinônimos e ajustar período e campo. Também mostra a string de cada base com copiar, abrir no site e edição manual, as notas de dialeto e, depois da busca, como o PubMed interpretou a string e o que ele não encontrou. A exportação JSON registra o plano editado e as strings efetivamente enviadas.
- **Linha de comando:** `nutev plan-query "pergunta" [--field-mode broad] [--include-pt] [--json]`.
- **Navegador = Python:** `apps/nutev-open/planner.js` é verificado contra o Python em 25 perguntas × 3 combinações de opções (`nutev_tests/test_question_planner.py`).

### 2.4 Achados resolvidos e abertos

| # | Situação após esta entrega |
| --- | --- |
| A1, A2, A3 | Resolvidos no Explorador Aberto e na CLI. A busca rápida hospedada continua em modo passthrough: mudar isso altera produção e deve ser decidido explicitamente (ver 3.1). |
| A4 | Contornado no planejador: termos em português vão para BVS/SciELO; às bases internacionais só vão quando a pessoa pede. O teste antigo do compilador hospedado permanece, por ser contrato do modo avançado. |
| A5 | Não se repete no planejador (truncamento preservado ou convertido por base). `topic_audit` continua como está. |
| A6 | Resolvido no planejador (`*` → `$` em BVS/SciELO; removido no OpenAlex/Crossref). |
| A9 | Resolvido no Explorador Aberto (tradução e avisos do PubMed exibidos). |
| A12 | Resolvido no Explorador Aberto (período por base; Crossref via `query.bibliographic`). |
| A7, A8, A10, A11 | Abertos (ver 3). |

## 3. Recomendações

1. **Busca hospedada:** oferecer "Interpretar pergunta" no modo rápido, usando `plan_question` + `to_review_strategy` para preencher o modo avançado, com a revisão visível antes de executar. Não substituir o passthrough silenciosamente.
2. **Vazio ≠ falha (A8):** usar os adaptadores com estado (`status_adapters.py`) no caminho web, para que falha de conector nunca apareça como "nenhum resultado".
3. **Correspondência por palavra inteira (A11):** avaliar trocar `term in title` por fronteira de palavra na classificação. Isso muda o score, então exige testes, versão de taxonomia e documentação, conforme `AGENTS.md`.
4. **Fontes regionais (A7):** tornar `lang` configurável, não envolver strings compiladas em `subject:(...)` e registrar quando só a primeira página foi lida.
5. **Histórico (A10):** salvar e restaurar a estratégia (avançada/exata ou plano) junto com a pergunta.
6. **Vocabulário:** revisão humana dos 113 conceitos; versão nova a cada mudança de significado; acompanhar as palavras descartadas e os termos livres mais frequentes para decidir novos conceitos.

## 4. Limites

- O planejador reconhece o que está no vocabulário. O que não está vira termo livre, visível e editável, e não é tratado como erro.
- A string gerada é um ponto de partida para busca exploratória e para leitura. Ela não é estratégia de revisão sistemática validada por PRESS.
- Sinônimos curados não garantem recall: mudanças de indexação e de vocabulário das bases continuam fora do controle do NutEV.
- Nenhuma decisão de elegibilidade, qualidade metodológica, certeza ou recomendação é derivada do plano de busca.
