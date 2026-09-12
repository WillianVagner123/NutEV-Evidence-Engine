# NutEV Reference Engine

**Descoberta, normalização, rastreabilidade, deduplicação, classificação e priorização de referências para Nutrição do Estilo de Vida.**

> **Versão de software:** 1.1.0  
> **Estado operacional:** produção aceita  
> **Estado de publicação:** GitHub Release `v1.1.0` publicada  
> **Estado de arquivo:** Zenodo/DOI da `v1.1.0` ainda não verificado  
> **SHA imutável da release e produção homologada:** `49588233ad2828b8fcc6140398ab55aedf7c03ef`  
> **Release histórica anterior:** `v1.0.0`  
> **DOI histórico de v1.0.0:** `10.5281/zenodo.21998607`  
> **Python:** 3.12–3.13  
> **Licença:** MIT

O **NutEV Reference Engine** é uma plataforma de recuperação de informação para
encontrar, organizar e auditar referências candidatas. O Engine coleta registros
em múltiplas fontes, normaliza metadados, aplica guardrails de rastreabilidade,
deduplica por identidade canônica, classifica pela taxonomia NutEV e gera filas
técnicas de leitura e exportação.

O score **não** representa qualidade metodológica, elegibilidade científica,
certeza da evidência, força de recomendação ou recomendação clínica.

## Estado atual

A versão 1.1.0 concluiu a aceitação operacional hospedada em modo multiusuário
provisionado e foi publicada no GitHub como release estável em 12 de setembro de
2026. A tag imutável `v1.1.0` aponta exatamente para:

```text
49588233ad2828b8fcc6140398ab55aedf7c03ef
```

O mesmo SHA passou pelos sete workflows obrigatórios, pelo deploy de produção e
pelo auditor pós-deploy read-only antes da publicação. A release pública inclui
wheel, sdist, hashes SHA-256, auditoria de distribuição, auditoria de container,
evidência de pré-requisitos e um manifesto sanitizado de release.

Estado de arquivo acadêmico:

- GitHub tag `v1.1.0`: **PUBLICADA**;
- GitHub Release `v1.1.0`: **PUBLICADA**;
- Zenodo/arquivo version-specific de `v1.1.0`: **PENDENTE / NÃO VERIFICADO**;
- DOI version-specific de `v1.1.0`: **AUSENTE ATÉ EMISSÃO REAL**;
- o DOI `10.5281/zenodo.21998607` permanece exclusivo da `v1.0.0`.

Release: `https://github.com/WillianVagner123/NutEV-Evidence-Engine/releases/tag/v1.1.0`

Veja `docs/RELEASE_NOTES_1_1_0.md`, `docs/FINAL_SYSTEM_ACCEPTANCE.md` e
`docs/PUBLICATION_READINESS.md`.

## Estado científico

Aceitação/publicação de software e validade científica são gates diferentes.

O estado de validação científica geral permanece:

```text
B — DEMOTE
```

Isto significa que o Engine funciona como software operacional de recuperação e
priorização, mas seu benefício científico incremental sobre comparadores ainda
precisa ser demonstrado pelo protocolo de validação em `validation/`.

### A1 e A2

A1 e A2 são aplicações científicas privadas que utilizam o Engine; não definem o
comportamento genérico da plataforma.

- **A1:** permanece dependente de revisão humana real e dos gates acadêmicos
  aplicáveis, incluindo PRESS/GF-10/freeze antes de qualquer promoção de busca
  formal/PRISMA.
- **A2:** permanece fail-closed enquanto a proveniência histórica necessária ao
  `LegacyBindingEvidence` não for demonstrada e revisada.
- O auditor pós-deploy da release 1.1.0 executou em modo read-only e encontrou
  zero ResearchApplications A1 e zero A2 materializadas. Nenhum binding, busca ou
  estado científico foi criado por inferência.

## Fluxo canônico

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

No Windows:

```text
Iniciar-NutEV-Windows.bat
  -> RODAR_TUDO.cmd
     -> run_everything_now.cmd
        -> tools/run_everything_now.py
     -> tools/run_latin_sources.py
     -> tools/rank_references.py
```

## Produto web e multi-tenancy

A hospedagem 1.1.0 usa `NUTEV_AUTH_MODE=pilot` e acesso provisionado. Não há
promessa de cadastro público automático.

A camada hospedada separa:

```text
user
  -> workspace
     -> project
        -> ResearchApplication
           -> private scientific state
```

Identidade bibliográfica global pode ser compartilhável, mas projeto, busca,
revisão, bindings, decisões humanas e outputs privados são escopados ao contexto
autorizado.

Os testes de release incluem Chromium autenticado, troca de workspace/projeto,
logout/stale-tab, lifecycle de busca/export e death tests multi-tenant.

## Primeiro uso

Quando uma conta não possui workspace/projeto provisionado, a interface deve
explicar o bloqueio em vez de apresentar um vazio ambíguo. O fluxo esperado é:

```text
login
  -> selecionar workspace
  -> selecionar projeto
  -> configurar aplicação/contexto
  -> busca
  -> Library
  -> revisão/exportação
```

Provisionamento de conta/workspace/projeto é administrativo.

## Pacote Python

A distribuição `nutev-nutmev` contém biblioteca e CLI reutilizáveis. Wheel/sdist
não devem conter contas, bancos, buscas privadas, configurações científicas A1/A2
nem backups do servidor.

A interface web e as ferramentas operacionais hospedadas são implantadas a partir
do commit revisado do repositório; elas não fazem parte do wheel.

## Instalação local

Primeira instalação no Windows:

```bat
git clone https://github.com/WillianVagner123/NutEV-Evidence-Engine.git
cd NutEV-Evidence-Engine
Iniciar-NutEV-Windows.bat
```

Repositório já instalado:

```bat
cd %USERPROFILE%\NutEV-Evidence-Engine
git checkout main
git pull --ff-only origin main
git rev-parse HEAD
Iniciar-NutEV-Windows.bat
```

Para reproduzir especificamente a release publicada:

```bat
git fetch --tags origin
git checkout v1.1.0
git rev-parse HEAD
```

O SHA esperado para `v1.1.0` é:

```text
49588233ad2828b8fcc6140398ab55aedf7c03ef
```

Para auditoria, preserve o SHA junto com os manifests e outputs daquela execução.

## Saídas principais

```text
project_output_reference/reference_ranking/TOP_REFERENCIAS.md
project_output_reference/reference_ranking/reference_ranking.csv
project_output_reference/reference_ranking/reference_ranking.jsonl
project_output_reference/reference_ranking/reference_quarantine.jsonl
project_output_reference/reference_ranking/AUDIT_MANIFEST.json
project_output_reference/reference_ranking/latest.json
```

- `TOP_REFERENCIAS.md`: fila TOP N para priorização de leitura;
- `reference_ranking.csv`: tabela completa para inspeção;
- `reference_ranking.jsonl`: saída estruturada;
- `reference_quarantine.jsonl`: itens bloqueados por guardrail;
- `AUDIT_MANIFEST.json`: hashes, política, fontes, contagens e assertions;
- `latest.json`: resumo da execução.

## Guardrails de rastreabilidade

O comportamento padrão é fail-closed.

Um registro precisa de provider, título e rota rastreável. Classes principais:

- `A_IDENTIFIER`: DOI, PMID ou PMCID sintaticamente plausível;
- `B_TRACEABLE_URL`: URL HTTP/HTTPS válida quando não há identificador válido;
- `Q_INCOMPLETE_ORIGIN`: provider ou título ausente;
- `Q_INVALID_IDENTIFIER`: identificador presente porém malformado, sem URL válida;
- `Q_UNTRACEABLE`: sem identificador válido e sem URL rastreável.

Registros `Q_*` ficam fora do ranking por padrão. O Engine não inventa ou repara
identificadores para remover itens da quarentena.

Validação sintática não prova que um DOI/PMID/PMCID resolve para o documento
correto; isso permanece uma limitação explícita.

## Identidade e deduplicação

Coleta e ranking usam o contrato em `src/nutev/reference_identity.py`:

```text
DOI válido
  -> PMID válido
  -> URL HTTP(S) normalizada
  -> título normalizado
```

A regra é determinística. Ela não equivale a deduplicação semântica/work-level
completa; versões, traduções ou manifestações com identificadores distintos ainda
podem permanecer separadas.

## Taxonomia

Registry ativo:

```text
config/taxonomy_registry.json
```

Versão canônica atual:

```text
2026-08-v2
```

Dimensões principais:

```text
domain
context
condition
outcome
```

A taxonomia descreve **sobre o que** o documento trata. Não representa nível de
evidência nem qualidade científica.

## Ranking

O score combina sinais explícitos de taxonomia, focus keywords, tipo documental,
provider, identificador válido, recência e penalidades de metadados.

Faixas atuais:

- `A_TOP_REFERENCE`: posições 1–20;
- `B_STRONG_REFERENCE`: posições 21–100;
- `C_DISCOVERY`: posições seguintes.

Essas faixas indicam prioridade técnica de leitura. `score_breakdown` registra a
contribuição de cada componente.

## Providers

Conforme disponibilidade/configuração:

- PubMed;
- Europe PMC;
- OpenAlex;
- Crossref;
- DOAJ;
- Semantic Scholar;
- fontes oficiais configuradas;
- LILACS/BVS e SciELO por rota nativa;
- Google Programmable Search, Brave e SerpAPI quando há credenciais.

Providers opcionais sem credencial são registrados como `skipped_config`, não
como buscas fictícias com zero resultados.

Scopus e Web of Science não são simulados. Sem acesso/licença configurada, o
Engine registra a indisponibilidade.

## Perfil profundo

```bat
set NUTEV_DEEP_COLLECTION=1
Iniciar-NutEV-Windows.bat
```

Para voltar ao perfil padrão:

```bat
set NUTEV_DEEP_COLLECTION=
```

O perfil profundo aumenta limites de coleta, mas não transforma uma execução em
busca exaustiva formal.

## Produção, deploy e recovery

O release pipeline hospedado segue, em alto nível:

```text
required CI/security/browser gates
  -> exact-SHA release barrier
  -> recovery readiness
  -> trusted SSH + 80/443 inventory
  -> protected snapshot
  -> bounded restore rehearsal
  -> deploy
  -> local/public smoke
  -> read-only post-deploy audit
```

A release `v1.1.0` foi publicada apenas depois de esse encadeamento passar para o
SHA exato `49588233ad2828b8fcc6140398ab55aedf7c03ef`.

A política de recovery preserva três snapshots completos e protege o release
ativo. Higiene de espaço pode remover apenas artefatos explicitamente seguros,
como cache Docker de build não utilizado; volumes científicos e snapshots válidos
não são tratados como cache.

## Auditoria

Cada execução bem-sucedida de ranking registra política de guardrails, versão da
taxonomia, hashes de configuração/input/output, contagens e assertions de runtime.

A GitHub Release `v1.1.0` também preserva artefatos específicos de publicação:

- wheel e sdist auditados;
- `SHA256SUMS.txt`;
- `distributions.json`;
- `release-evidence.json`;
- `container-audit.zip`;
- `release-prerequisites.zip`.

Auditabilidade prova integridade e proveniência do pipeline em relação aos
manifests. Ela **não prova verdade bibliográfica ou validade científica**.

Documentos principais:

- `docs/AUDITABILITY_AND_GUARDRAILS.md`;
- `docs/ARCHITECTURE.md`;
- `docs/TAXONOMY.md`;
- `docs/KNOWN_LIMITATIONS.md`;
- `docs/FINAL_SYSTEM_ACCEPTANCE.md`;
- `docs/PUBLICATION_READINESS.md`;
- `docs/RELEASE_NOTES_1_1_0.md`.

## Validação científica

O projeto não deve ser promovido acima de `B — DEMOTE` apenas porque CI,
produção, Windows smoke, hashes ou publicação de software passam.

A validação planejada inclui, entre outros itens:

- gold standard independente;
- comparadores/baselines;
- precision/recall@k;
- MAP, MRR e nDCG;
- ablation study;
- validação humana da taxonomia;
- benchmark de deduplicação;
- contribuição marginal por provider;
- auditoria de perda de recall por quarentena;
- sensibilidade do ranking;
- conjunto externo selado;
- estudo de workload quando aplicável.

Arquivos canônicos:

```text
validation/SCIENTIFIC_VALIDATION_PROTOCOL.md
validation/SCIENTIFIC_VALIDATION_STATUS.md
validation/GOLD_STANDARD_PROTOCOL.md
validation/BENCHMARK_PLAN.md
validation/SCIENTIFIC_VALIDATION_REPORT.md
```

## O que o NutEV não é

O NutEV Reference Engine não é:

- revisão sistemática/scoping review automática;
- mecanismo PRISMA automático;
- avaliador automático de risco de viés;
- avaliador automático de qualidade metodológica;
- sistema de recomendação clínica;
- substituto da leitura crítica humana;
- simulador de bases licenciadas indisponíveis;
- gerador de referências por IA.

## Desenvolvimento

```bash
python -m pip install -e ".[dev]"
PYTHONPATH=src python -m pytest -q nutev_tests
python -m compileall -q src tools nutev_tests
ruff check src tools nutev_tests --select F,E9
```

O CI cobre Python 3.12/3.13, Windows smoke, lint/compile, typecheck, guardrails,
security scan, dependency review, CodeQL, artefatos de release, Chromium e gates
multi-tenant.

## Releases

### v1.1.0 — release atual

- GitHub tag: `v1.1.0`;
- SHA: `49588233ad2828b8fcc6140398ab55aedf7c03ef`;
- GitHub Release: `https://github.com/WillianVagner123/NutEV-Evidence-Engine/releases/tag/v1.1.0`;
- publicada em: `2026-09-12`;
- Zenodo/DOI específico: **ainda não verificado / não registrar até emissão real**.

### v1.0.0 — histórica

- GitHub Release: `https://github.com/WillianVagner123/NutEV-Evidence-Engine/releases/tag/v1.0.0`;
- Zenodo: `https://zenodo.org/records/21998607`;
- DOI: `10.5281/zenodo.21998607`.

A tag `v1.1.0` é imutável e não deve ser movida para commits posteriores de
documentação. Um eventual DOI da 1.1.0 deve ser adicionado somente depois de um
registro de arquivo real ser publicado e verificado.
