# Explorador Aberto de Evidências (Open Evidence Explorer)

O Explorador Aberto é a superfície **pública, sem login e sem servidor** do NutEV. Qualquer pessoa pode buscar literatura de Medicina do Estilo de Vida (MEV) e Nutrição do Estilo de Vida (NEV) e entender a **qualidade do dado** de cada registro com as mesmas regras públicas e auditáveis do Reference Engine.

```text
apps/nutev-open/
  index.html                 página única (PT-BR padrão, EN opcional)
  core.js                    port fiel das regras do Engine (rastreabilidade, identidade, taxonomia, prioridade)
  planner.js                 pergunta -> blocos PICO -> uma string por base (port de question_planner.py)
  sources.js                 acesso às fontes abertas (único arquivo com rede)
  app.js                     interface
  i18n.js                    textos PT/EN
  presentation.json          rótulos de apresentação (famílias MEV/NEV, rótulos EN)
  data/nutev-open-data.js    pacote de regras GERADO a partir da configuração canônica
  build-info.js              identidade da publicação (sobrescrito no deploy)
```

## Busca por pergunta

A pessoa escreve do jeito dela, em português ou inglês. O planejador determinístico (`src/nutev/search/question_planner.py`, com port em `planner.js`) faz o seguinte:

- reconhece conceitos do vocabulário curado `config/query_vocabulary.json`;
- separa população, intervenção, comparador, contexto, desfecho, tipo de estudo e termos livres;
- entende períodos ("desde 2015", "nos últimos 5 anos");
- monta uma string por base, no formato da base:
  - PubMed: `[tiab]`/`[pt]`/`[dp]`;
  - Europe PMC: `TITLE_ABS`/`PUB_YEAR`;
  - OpenAlex: booleana mais filtros de data;
  - Crossref: palavras-chave mais filtro de data;
  - BVS/LILACS: `tw:` com `$`;
  - SciELO: booleana com `$`.

O painel "Como o NutEV organizou sua busca" mostra tudo e deixa editar: blocos, termos, período, campo, inclusão de termos em português e a própria string de cada base. Depois da busca, ele mostra como o PubMed interpretou a string. BVS/LILACS e SciELO são abertos no site da própria base.

Não há modelo de linguagem e MeSH/DeCS não são inventados. No modo "Ampla", é a própria base que aplica o vocabulário dela. Uma string avançada digitada (operadores, aspas, campos) é enviada literalmente. Auditoria e decisões: [`SEARCH_KEYWORD_AUDIT_2026-10.md`](SEARCH_KEYWORD_AUDIT_2026-10.md).

## O que a pessoa vê

| Leitura | Pergunta | Fonte da regra |
| --- | --- | --- |
| **Nível do dado A/B/Q** | O registro é rastreável? | `src/nutev/audit_guardrails.py::record_traceability` |
| **Completude dos metadados** | Quais dos 6 campos (título, resumo, ano, autores, periódico, identificador) existem? | descritiva, não pontua |
| **Eixos MEV/NEV** | Sobre o que o registro trata? | `config/taxonomy_registry.json` + `config/keyword_taxonomy*.json` |
| **Tipo documental** | Que tipo de documento parece ser? | `src/nutev/search/classification.py` (`nutev-document-class-v1`) |
| **Prioridade técnica de leitura** | Por que esta ordem? | `tools/rank_references.py::score_record` |

Níveis do dado (classes canônicas do gate de rastreabilidade):

- **A — Identificador verificável** (`A_IDENTIFIER`): DOI, PMID ou PMCID sintaticamente válido;
- **B — URL rastreável** (`B_TRACEABLE_URL`): sem identificador válido, com URL HTTP(S);
- **Q — Quarentena** (`Q_INCOMPLETE_ORIGIN`, `Q_INVALID_IDENTIFIER`, `Q_UNTRACEABLE`): fora da ordenação e visível com o motivo.

O **painel de qualidade** cruza os dois eixos pedidos pelo produto: para cada eixo da MEV e da NEV (pilares da MEV, padrões alimentares, composição, culinária/literacia, contexto, condição e desfecho), mostra quantas obras apareceram e a proporção A/B/Q, além de qualidade por fonte, completude por campo, tipo documental e ano.

## Fluxo

```text
QUESTION PLAN (pergunta -> blocos -> string por base)
  -> SEARCH (navegador -> Europe PMC, PubMed, OpenAlex, Crossref)
  -> NORMALIZE (sources.js)
  -> TRACEABILITY GATE (A/B/Q)
  -> DEDUPLICATE (DOI -> PMID -> URL; conflitos de identificador forte ficam separados)
  -> CLASSIFY (eixos MEV/NEV, tipo documental, completude)
  -> RANK (prioridade técnica de leitura)
  -> EXPORT (CSV / JSON com manifesto)
```

Também é possível abrir localmente `reference_ranking.jsonl`, `reference_ranking.csv`, `reference_quarantine.jsonl` ou um JSON exportado pelo próprio explorador. O arquivo é lido apenas no navegador; nada é enviado.

## Fonte única de verdade

`data/nutev-open-data.js` é **gerado**, nunca editado à mão:

```bash
python tools/build_open_explorer_data.py          # regenera
python tools/build_open_explorer_data.py --check  # falha se houver drift
```

O gerador compila a taxonomia com `load_canonical_taxonomy` (fail-closed), lê pesos e limites de `config/reference_mode.json`, importa os padrões de tipo documental do código Python e registra o SHA-256 de cada arquivo de configuração usado e do próprio pacote. Todo eixo canônico precisa de rótulo em inglês em `presentation.json`; caso contrário o gerador falha.

## Paridade Python ↔ JavaScript

`nutev_tests/test_open_explorer.py` executa o código do navegador em Node (`nutev_tests/fixtures/open_explorer_harness.cjs`) e compara com o Python, campo a campo:

- normalização de DOI, PMID, PMCID, URL, título e texto (`_norm`);
- classe de rastreabilidade e motivos;
- identidade canônica e deduplicação com proveniência (`source_providers`);
- score completo (`score_breakdown`), eixo principal, grupos, termos, ranks por eixo e ordenação;
- tipo documental;
- identificadores e URLs dos adaptadores de fonte.

O mesmo teste garante que a página é estática, com CSP restritiva (`connect-src` limitado às quatro APIs abertas), sem chamadas a back-end, sem cookies e sem endpoints de modelos de linguagem. O CI roda `--check` e a paridade no job `audit guardrail contract`.

Diferenças documentadas dos adaptadores do navegador em relação aos adaptadores Python (não alteram as regras de classificação):

- Europe PMC usa `resultType=core` (resumo e palavras-chave do autor);
- o resumo do OpenAlex é reconstruído na ordem de leitura a partir do índice invertido, e o PMID do OpenAlex é mantido;
- marcação HTML/JATS é removida de títulos e resumos;
- Crossref usa a data `issued` quando `published-print`/`published-online` estão ausentes.

## Fronteiras

- Fontes consultadas: Europe PMC, PubMed, OpenAlex e Crossref, com limite de 25/50/100 registros por fonte. Isso **não** é busca exaustiva nem busca formal de revisão sistemática.
- Scopus e Web of Science nunca são simulados; aparecem como "não consultados". LILACS/BVS, SciELO, DOAJ e Semantic Scholar continuam disponíveis no Reference Engine completo.
- Falhas, limites de requisição e bloqueios do navegador aparecem por fonte, explicitamente.
- O explorador não acessa estado privado: não usa workspace, projeto, ResearchApplication, Contexto de Evidências, A1/A2, bancos privados ou outputs de runtime.
- Nada é inferido sobre elegibilidade, qualidade metodológica, risco de viés, certeza, recomendação ou PRISMA. A prioridade de leitura e os níveis A/B/Q descrevem rastreabilidade e organização técnica dos metadados.
- Nenhum modelo de linguagem é usado: toda classificação é determinística e reproduzível.

## Uso local

Abra `apps/nutev-open/index.html` no navegador (Chrome/Edge) ou sirva a pasta:

```bash
python -m http.server 8000 --directory apps/nutev-open
# http://localhost:8000
```

## No site hospedado (Hetzner), sem login

No runtime hospedado (`apps/nutev-web/secure_server.py`), o explorador é servido em **`/aberto/`**, e qualquer pessoa usa sem conta e sem vínculo com workspace:

- `server.py` mapeia `/aberto` para `apps/nutev-open`, confinado a essa pasta;
- no modo `pilot`, `request_boundary.pilot_route_kind` trata `/aberto` e `/aberto/` como estáticos públicos. Arquivos fora das extensões estáticas (por exemplo `presentation.json`) continuam bloqueados;
- a CSP de `/aberto/*` permite `connect-src` apenas para as quatro APIs abertas. As demais páginas mantêm `connect-src 'self'`;
- o visitante anônimo de `/` ou `/index.html` é enviado para `/aberto/` (302). Quem já entrou continua vendo a home normal;
- o login só é necessário para a **busca avançada**: biblioteca, histórico, projetos, revisão e exportações privadas. O explorador mostra o atalho "Busca avançada (entrar)", e a tela de login e a home mostram "Buscar sem login";
- no proxy Caddy gerenciado, `basic_auth` vale para todas as rotas exceto `/aberto` e `/aberto/*`. Se a produção usar um proxy externo, a mesma exceção precisa ser configurada nele (o deploy avisa com `::notice::` quando `/aberto/` responde 401).

Testes: `nutev_tests/test_open_explorer_hosting.py` (servidor pilot real, visitante anônimo) e `nutev_tests/test_hetzner_autodeploy.py`.

## Publicação

`.github/workflows/open-explorer-pages.yml` publica a pasta no GitHub Pages a cada push em `main` que toque o explorador, a configuração canônica ou o código de classificação. O workflow repete `--check` e os testes de paridade antes de publicar e grava o SHA do commit em `build-info.js`.

Configuração única no repositório: **Settings → Pages → Build and deployment → Source: GitHub Actions**. Endereço esperado: `https://willianvagner123.github.io/NutEV-Evidence-Engine/`.

A publicação da página não altera a release imutável `v1.1.0`, o DOI arquivado nem o estado científico (`B — DEMOTE`).
