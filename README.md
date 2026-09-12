# NutEV Reference Engine

**Descoberta, normalização, rastreabilidade, deduplicação, classificação e priorização de referências para Nutrição do Estilo de Vida.**

## Estado atual

| Superfície | Estado |
|---|---|
| Site / software NutEV 1.1.0 em produção | **PASS — FECHADO** |
| SHA homologado em produção | `e40dfd8c48cde824fa6053f9b077157f21bae698` |
| Deploy exato homologado | `#1659` — **PASS** |
| Auditor pós-deploy | `#99` — **PASS** |
| GitHub tag / Release `v1.1.0` | **PENDENTE DE PUBLICAÇÃO** |
| Zenodo / DOI específico da `v1.1.0` | **PENDENTE — não reutilizar DOI antigo** |
| Release pública arquivada anterior | `v1.0.0` |
| DOI da `v1.0.0` | `10.5281/zenodo.21998607` |
| Validação científica do Engine | **B — DEMOTE** |
| A1 / A2 | **gates científicos independentes / fail-closed** |
| Python | **3.12–3.13** |
| Licença | **MIT** |

**Produção concluída não é sinônimo de publicação acadêmica concluída.** A versão 1.1.0 está homologada e ativa no servidor, mas só deve ser descrita como `RELEASED/PUBLISHED` depois de existirem, de fato, a tag imutável `v1.1.0`, o GitHub Release e o novo registro de arquivo/DOI correspondente. O DOI histórico da `v1.0.0` não pertence à `v1.1.0`.

O fechamento operacional está documentado em `docs/releases/v1.1.0-production-closeout.md`. A preparação para publicação fica em `docs/PUBLICATION_READINESS.md`.

## O que é o NutEV

O **NutEV Reference Engine** é um software de recuperação de informação para encontrar e organizar referências candidatas. Ele coleta registros em múltiplas fontes, normaliza metadados, aplica guardrails de rastreabilidade, deduplica por uma regra canônica de identidade, classifica pela taxonomia NutEV e gera uma fila técnica de leitura.

O score **não** representa qualidade metodológica, elegibilidade científica, certeza da evidência, força de recomendação ou recomendação clínica.

## Estado científico atual

O projeto permanece sob protocolo explícito de validação científica. O estado atual do Engine continua:

```text
B — DEMOTE
```

Isto significa que o software funciona como utilitário operacional, mas seu benefício científico incremental sobre baselines e ferramentas existentes **ainda não foi demonstrado**.

A homologação de produção 1.1.0 **não promove** esse estado. A1 e A2 também não são materializados por inferência: sem evidência humana/proveniência válida, permanecem bloqueados.

Arquivos científicos canônicos:

```text
validation/SCIENTIFIC_VALIDATION_PROTOCOL.md
validation/SCIENTIFIC_VALIDATION_STATUS.md
validation/GOLD_STANDARD_PROTOCOL.md
validation/BENCHMARK_PLAN.md
validation/SCIENTIFIC_VALIDATION_REPORT.md
```

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

## Pacote Python e produto web

A distribuição `nutev-nutmev` contém a biblioteca Python e o CLI. O wheel/sdist não contém contas, bancos, buscas privadas, configurações de pesquisa A1/A2 ou backups.

A interface web, seus scripts e configurações são implantados a partir do commit revisado do repositório; não fazem parte do wheel. O modo multiusuário é de acesso provisionado administrativamente, não cadastro público automático.

A produção 1.1.0 foi homologada com:

- 7/7 workflows no mesmo SHA;
- recovery readiness no Hetzner;
- capacidade suficiente para snapshot;
- três snapshots completos preservados;
- release ativo protegido;
- Caddy externo em 80/443;
- `/search.html` e `/articles.html` respondendo `200`;
- superfícies privadas sem autenticação respondendo `401` / fail-closed;
- backup/restore real aprovado;
- 19.466 arquivos verificados;
- 33 bancos SQLite verificados;
- `production_overwritten=false`;
- auditor pós-deploy executado de verdade, sem alteração do estado científico e sem Legacy Binding implícito.

## Instalação e execução

Primeira instalação:

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

Para auditoria, preserve o SHA mostrado por `git rev-parse HEAD` junto com manifests e outputs daquela execução.

## Saídas principais

```text
project_output_reference/reference_ranking/TOP_REFERENCIAS.md
project_output_reference/reference_ranking/reference_ranking.csv
project_output_reference/reference_ranking/reference_ranking.jsonl
project_output_reference/reference_ranking/reference_quarantine.jsonl
project_output_reference/reference_ranking/AUDIT_MANIFEST.json
project_output_reference/reference_ranking/latest.json
```

- `TOP_REFERENCIAS.md`: TOP N para priorização de leitura.
- `reference_ranking.csv`: tabela completa para inspeção/planilha.
- `reference_ranking.jsonl`: saída estruturada.
- `reference_quarantine.jsonl`: registros bloqueados pelo gate.
- `AUDIT_MANIFEST.json`: hashes, política, fontes, contagens e assertions.
- `latest.json`: resumo da execução.

## Guardrails de rastreabilidade

O comportamento padrão é fail-closed.

Um registro precisa de provider, título e uma rota rastreável. As classes são:

- `A_IDENTIFIER`: DOI, PMID ou PMCID sintaticamente plausível;
- `B_TRACEABLE_URL`: URL HTTP/HTTPS válida quando não há identificador válido;
- `Q_INCOMPLETE_ORIGIN`: provider ou título ausente;
- `Q_INVALID_IDENTIFIER`: identificador presente, porém malformado, sem URL HTTP/HTTPS válida;
- `Q_UNTRACEABLE`: sem identificador válido e sem URL HTTP/HTTPS válida.

Registros `Q_*` ficam fora do ranking por padrão. O Engine não inventa nem repara identificadores para retirar um item da quarentena.

## Identidade e deduplicação

Coleta e ranking usam o mesmo contrato canônico em `src/nutev/reference_identity.py`:

```text
DOI válido
  -> PMID válido
  -> URL HTTP(S) normalizada
  -> título normalizado
```

A regra é determinística. Quando duas manifestações têm a mesma identidade, o Engine preserva preferencialmente o registro com texto descritivo mais rico.

Isto **não** é deduplicação semântica/work-level completa.

## Taxonomia e ranking

A classificação ativa é controlada por:

```text
config/taxonomy_registry.json
```

Versão canônica atual:

```text
2026-08-v2
```

Dimensões:

```text
domain
context
condition
outcome
```

O score combina sinais explícitos de correspondência taxonômica, palavras-chave foco, tipo documental textual, provider, identificador válido, recência e penalidades por metadados ausentes.

Faixas atuais:

- `A_TOP_REFERENCE`: posições 1–20;
- `B_STRONG_REFERENCE`: posições 21–100;
- `C_DISCOVERY`: posições seguintes.

Essas faixas significam **prioridade técnica de leitura**, não força científica.

## Fontes suportadas

O perfil operacional integra, conforme disponibilidade/configuração:

- PubMed;
- Europe PMC;
- OpenAlex;
- Crossref;
- DOAJ;
- Semantic Scholar;
- fontes oficiais configuradas;
- LILACS/BVS e SciELO por rota nativa;
- Google Programmable Search, Brave e SerpAPI quando há credenciais.

Scopus e Web of Science não são simulados. Ausência de credencial é registrada como indisponibilidade/skipped quando aplicável, não como falsa ausência de evidência.

## Auditoria e recuperação

Cada execução bem-sucedida de ranking registra política de guardrails, versão/modo da taxonomia, hashes das configurações, hashes dos masters de entrada, contagens de rastreáveis/quarentena, hashes dos outputs e assertions do runtime.

A auditabilidade prova integridade e proveniência em relação aos manifests. Ela **não prova verdade bibliográfica ou validade científica**.

A homologação de produção também validou recuperação real sem sobrescrever o volume de produção. A política de capacidade remove apenas cache Docker de build não utilizado e preserva os três pontos completos de rollback.

Veja:

- `docs/AUDITABILITY_AND_GUARDRAILS.md`;
- `docs/ARCHITECTURE.md`;
- `docs/TAXONOMY.md`;
- `docs/KNOWN_LIMITATIONS.md`;
- `docs/ROLLBACK_RUNBOOK.md`;
- `docs/HETZNER_AUTODEPLOY.md`.

## O que este projeto não é

O NutEV Reference Engine não é:

- revisão sistemática/scoping review automática;
- mecanismo PRISMA;
- avaliador de risco de viés;
- avaliador automático de qualidade metodológica;
- sistema de recomendação clínica;
- substituto de leitura crítica humana;
- simulador de bases licenciadas indisponíveis;
- gerador de referências por IA.

## Desenvolvimento

```bash
python -m pip install -e ".[dev]"
PYTHONPATH=src python -m pytest -q nutev_tests
python -m compileall -q src tools nutev_tests
ruff check src tools nutev_tests --select F,E9
```

O CI inclui testes em Python 3.12/3.13, Windows smoke, contrato de guardrails, typecheck, lint/compile, security scan, dependency review, CodeQL e validação de artefatos de release.

## Release e publicação

### Produção 1.1.0

A aplicação em produção está homologada no commit imutavelmente identificado por:

```text
e40dfd8c48cde824fa6053f9b077157f21bae698
```

Esse é o SHA que deve ser usado como alvo da futura tag `v1.1.0`.

### Publicação 1.1.0

Enquanto a tag e o GitHub Release `v1.1.0` não existirem e o novo depósito de arquivo não tiver sido verificado, o estado público correto é:

```text
PRODUCTION_ACCEPTED / PUBLICATION_PENDING
```

Não atribua à 1.1.0 o DOI `10.5281/zenodo.21998607`; esse DOI permanece ligado à versão histórica `v1.0.0`.

### Release histórica 1.0.0

A tag/release `v1.0.0` é histórica e não deve ser movida ou recriada.

Release: `https://github.com/WillianVagner123/NutEV-Evidence-Engine/releases/tag/v1.0.0`  
Zenodo: `https://zenodo.org/records/21998607`

## Documentos de fechamento

- `docs/releases/v1.1.0-production-closeout.md` — fechamento operacional canônico da 1.1.0;
- `docs/PUBLICATION_READINESS.md` — o que ainda falta para `RELEASED/PUBLISHED`;
- `docs/SYSTEM_CLOSEOUT_MASTER.md` — ledger geral de fechamento;
- `docs/FINAL_SYSTEM_ACCEPTANCE.md` — aceite final do site/software;
- `docs/OPEN_PR_DISPOSITION.md` — tratamento separado de backlog/PRs históricos.
