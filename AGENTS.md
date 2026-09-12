# AGENTS.md — NutEV Reference Engine

Este arquivo define o escopo e as invariantes que agentes automatizados devem preservar ao modificar este repositório.

## Produto suportado

O fluxo genérico suportado é:

```text
SEARCH -> NORMALIZE -> TRACEABILITY -> DEDUPLICATE -> CLASSIFY -> RANK -> EXPORT -> AUDIT
```

O NutEV coleta e organiza referências candidatas. Ranking indica prioridade técnica de leitura; não representa elegibilidade científica, qualidade metodológica, certeza da evidência, força de recomendação ou recomendação clínica.

## Invariantes não negociáveis

1. Nunca fabricar provider results, contagens, identificadores, URLs, DOIs, PMIDs, afiliações, funding, autoria ou evidência de execução.
2. Falhas, rate limits, ausência de credenciais e mudanças de interface devem permanecer explícitos.
3. Scopus e Web of Science nunca devem ser simulados.
4. `source` / `source_provider` deve sobreviver ao fluxo até os outputs.
5. Queries, limites, taxonomia, pesos, manifests e hashes relevantes devem permanecer versionados/inspecionáveis.
6. A identidade atual é determinística (`DOI -> PMID -> URL -> título normalizado`) e não deve ser descrita como deduplicação semântica/work-level completa.
7. Mudanças de scoring/identidade/taxonomia devem atualizar testes e documentação arquitetural aplicável.
8. Outputs públicos devem respeitar as allowlists/guardrails do produto.
9. Nunca versionar segredos, bancos privados, backups ou texto completo sem direito de redistribuição.
10. Seleção de workspace/projeto não é autorização; identidade e escopo privado são resolvidos no servidor.
11. `PLATFORM_ADMIN` não é bypass implícito para estado científico privado.
12. Configuração/deploy de A1/A2 não cria aprovação científica, ownership histórico, PRISMA ou decisões humanas por inferência.
13. Tags e releases publicadas são imutáveis.

## Contexto compartilhado para agentes

Para qualquer trabalho, comece por:

1. `AI_CONTEXT.md` — ponto de entrada compartilhado;
2. `README.md` — produto/release/produção atuais;
3. `docs/README.md` — índice da documentação viva.

Para Artigo 1, use também:

1. `ARTICLE1_SEARCH_MASTER.md`;
2. `config/nutev/article1_search_master_v1.json`;
3. quando existir, `project_output_reference/agent_context/article1/CONTEXT_MANIFEST.json` e `SEARCH_STATE.json`.

O bundle de agentes é privado e serve para navegação/contexto. Ele não autoriza PRESS, GF-10, freeze, inclusão/exclusão, avaliação de qualidade, recomendação ou PRISMA.

Documentos em `docs/archive/` são evidência histórica/proveniência; não substituem contratos vivos de `main`.

## Runtime e configuração canônicos

Entrypoints e configurações principais incluem:

```text
Iniciar-NutEV-Windows.bat
RODAR_TUDO.cmd
run_everything_now.cmd
tools/run_everything_now.py
tools/run_latin_sources.py
tools/rank_references.py
config/reference_search.json
config/reference_mode.json
config/keyword_taxonomy*.json
src/nutev/search/
```

A hospedagem multi-tenant aceita `legacy` como modo de compatibilidade no código, mas a linha de produção v1.1.0 usa `NUTEV_AUTH_MODE=pilot` e passa pelo gate exato de promoção definido em `docs/FINAL_MULTITENANT_RELEASE_GATE.md`.

## Outputs canônicos de ranking

```text
project_output_reference/reference_ranking/TOP_REFERENCIAS.md
project_output_reference/reference_ranking/reference_ranking.csv
project_output_reference/reference_ranking/reference_ranking.jsonl
project_output_reference/reference_ranking/reference_quarantine.jsonl
project_output_reference/reference_ranking/AUDIT_MANIFEST.json
project_output_reference/reference_ranking/latest.json
```

Outputs de runtime são artefatos operacionais/privados conforme o contexto e não devem ser confundidos com conteúdo apropriado para o pacote público.

## Workflow de mudança

Para alterações não triviais:

1. verificar o SHA atual de `main`;
2. criar branch dedicada;
3. limitar o diff ao escopo declarado;
4. adicionar/ajustar testes quando o contrato muda;
5. atualizar documentação pública/operacional correspondente;
6. obter os gates exigidos no mesmo SHA candidato;
7. abrir/revisar PR;
8. não fazer merge com gates necessários falhando;
9. após merge/deploy, diferenciar o SHA móvel de produção do snapshot imutável da release;
10. nunca mover tags publicadas.

## Mudanças de provider/ranking

Mudanças de provider devem preservar identidade, falha explícita, ausência de fallback silencioso rotulado como outro provider e os controles de acesso aplicáveis.

Se alterar taxonomia, pesos, focus terms, tipo documental, recência, identidade/deduplicação, tiers ou schema, revisar testes, `docs/ARCHITECTURE.md`, `docs/KNOWN_LIMITATIONS.md` e documentação operacional/README quando houver efeito visível ao usuário.

## Fronteira científica

Software verde, deploy verde, Windows smoke, hashes e publicação não promovem a validação científica acima do que o protocolo suporta.

O estado geral permanece `B — DEMOTE` até evidência de validação científica justificar mudança.

A1 continua dependente de revisão humana e gates acadêmicos reais; A2 continua fail-closed para binding histórico sem proveniência revisada. Nenhum agente deve preencher esses gates por inferência.

## Release atual

```text
versão: 1.1.0
tag imutável: v1.1.0
release SHA: 49588233ad2828b8fcc6140398ab55aedf7c03ef
GitHub Release: publicada em 2026-09-12
Zenodo record: 22726717
DOI version-specific: 10.5281/zenodo.22726717
produção: aceita
```

A `main` pode avançar por correções/documentação pós-release e ser novamente implantada após os gates do novo SHA. Isso não altera o snapshot, tag, GitHub Release ou arquivo Zenodo de `v1.1.0`.

### Release histórica anterior

```text
versão: 1.0.0
tag: v1.0.0
release SHA: 5728d79b05e618897f01ba93886a17584c9f215f
Zenodo record: 21998607
DOI: 10.5281/zenodo.21998607
```

O DOI da v1.0.0 não deve ser reutilizado como DOI da v1.1.0 ou de release futura.

## Futuras releases

Versão, tag, GitHub Release, `CITATION.cff`, `.zenodo.json`, changelog e release notes devem se referir à mesma identidade de release. Um DOI version-specific só deve ser registrado depois de realmente emitido/verificado pelo serviço de arquivo.
