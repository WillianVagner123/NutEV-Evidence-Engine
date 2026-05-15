# NutMEV Deep Research Engine

Sistema local e automatizado para busca, vigilância, captura, organização e síntese de evidências científicas relacionadas à Nutrição do Estilo de Vida, obesidade, risco cardiometabólico, padrões alimentares, adesão, food literacy, culinary medicine, comensalidade e construção do framework NutMEV.

## O que é este projeto

Este projeto possui duas camadas principais:

1. **Workstreams de tese/artigos**
   - `busca1`
   - `busca2a`
   - `busca2b`
   - `a3`

2. **NutMEV Global Watch**
   - vigilância científica contínua
   - providers reais
   - digest
   - captura opcional
   - webhook opcional
   - GitHub Actions semanal

## Agradecimento e inspiração

Este projeto foi arquiteturalmente inspirado no projeto open-source **Local Deep Research** (comunidade LearningCircuit), especialmente na ideia de pesquisa profunda local com múltiplas fontes e automação.

O NutMEV adapta esses princípios para um caso científico específico: revisão, vigilância e síntese de evidências em Nutrição do Estilo de Vida e cardiometabolismo. Não é uma cópia 1:1 do README original.

## Arquitetura atual

- `src/nutev/engine`: contratos canônicos, `SearchCase`, `SearchJob`, `RunEvent`, artifact manifest.
- `src/nutev/global_watch`: pipeline watch, query builder, scoring, captura, digest, webhook, export.
- `src/nutev/pipelines`: pipeline dos workstreams.
- `src/nutev/search`: PubMed, Europe PMC, OpenAlex, Crossref (quando disponível), fontes oficiais.
- `src/nutev/download`: resolver, downloader, filtros, dedup.
- `src/nutev/extract`: PDF, HTML, DOCX, planilhas, OCR.
- `src/nutev/analysis`: relevância, síntese, PRISMA, framework, qualificação.
- `src/nutev/export`: CSV, XLSX, Rayyan, logs, métodos e relatórios.

## Workstreams

### busca1
Diretrizes alimentares, literatura cinza, guias alimentares, obesidade não clínica e Nutrição do Estilo de Vida.

### busca2a
Diretrizes e consensos clínicos sobre obesidade com diabetes, hipertensão, dislipidemia, DAC, risco cardiovascular, síndrome metabólica e MASLD/NAFLD.

### busca2b
Intervenções dietéticas, padrões alimentares, adesão, implementação e desfechos metabólicos.

### a3 / artigo3_framework
Framework NutMEV, competências e instrumentos (incluindo food literacy, culinary medicine e comensalidade).

## NutMEV Global Watch

- Radar contínuo (não substitui revisão fechada).
- Busca novidades por providers e fontes oficiais.
- Compara com histórico (`seen_items`).
- Gera digest.
- Pode capturar PDF/HTML público.
- Pode enviar webhook.

## Instalação local (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
$env:PYTHONPATH="src"
```

Dependências-chave (quando necessário): `pandas`, `openpyxl`, `requests`, `beautifulsoup4`, `pydantic`, `pytest`, `pypdf`, `pdfplumber`, `pdf2image`, `Pillow`, `pytesseract`, `python-docx`.

## Comandos principais

### Rodar testes
```bash
PYTHONPATH=src python -m pytest -q nutev_tests -p no:timeout
```

### Rodar workstreams
```bash
PYTHONPATH=src python -m nutev.cli --project-root ./project_output --workstreams busca1 busca2a busca2b a3 --web-enabled
```

### Rodar Global Watch rápido
```bash
PYTHONPATH=src python -m nutev.cli global-watch --project-root ./project_output --since-days 7 --mode quick --web-enabled
```

### Rodar Global Watch com captura
```bash
PYTHONPATH=src python -m nutev.cli global-watch --project-root ./project_output --since-days 7 --mode quick --web-enabled --capture-enabled --capture-limit 5
```

### Rodar Global Watch com webhook
```bash
PYTHONPATH=src python -m nutev.cli global-watch --project-root ./project_output --since-days 7 --mode thesis --web-enabled --capture-enabled --notify-webhook
```

## Variáveis de ambiente

- `OPENAI_API_KEY`
- `NUTEV_DIGEST_WEBHOOK_URL`
- `NUTEV_NOTIFY_WEBHOOK`
- `GOOGLE_API_KEY`
- `GOOGLE_CSE_ID`
- `SERPAPI_API_KEY`
- `BRAVE_API_KEY`

OpenAI e webhook são opcionais; o pipeline foi desenhado para não quebrar sem essas variáveis.

## Saídas esperadas

- `project_output/02_metadata/`
- `project_output/03_corpus/`
- `project_output/05_extraction/`
- `project_output/06_tables/`
- `project_output/07_logs/`
- `project_output/08_docs/`
- `project_output/09_global_watch/`

Arquivos principais:
- `metadata_master.csv`
- `rayyan_ready.csv`
- `run_summary.json`
- `run_events.jsonl`
- `artifact_manifest.csv`
- `global_watch_master.csv`
- `global_watch_new_items.csv`
- `global_watch_digest.md`
- `NUTEV_GLOBAL_WATCH_LATEST.md`

## GitHub Actions

Workflow: `.github/workflows/nutev-global-watch.yml`
- execução manual;
- execução semanal (domingo 10:00 UTC);
- roda testes;
- roda Global Watch;
- sobe artifacts;
- pode enviar webhook se secrets estiverem configurados.

## Limitações importantes

- não faz bypass de paywall;
- não faz login institucional;
- não resolve CAPTCHA;
- respostas 403/404/400 viram `metadata_only`/`failure_reason`;
- OCR depende de Tesseract/Poppler instalados;
- captura browser/JS profundo não está completa;
- LLM/OpenAI é opcional.

## Ética e acesso

- scraping respeitoso;
- sem anti-bot bypass;
- preservação de rastreabilidade;
- falhas são registradas, não ocultadas.

## Status atual do projeto

| Componente | Status |
|---|---|
| Workstreams busca1/busca2a/busca2b/a3 | Implementado |
| Engine canônico | Implementado |
| Global Watch | Implementado |
| Providers reais | Parcial (depende de disponibilidade/rede/provider) |
| Capture layer | Implementado (em hardening contínuo) |
| Webhook | Implementado |
| OpenAI/LLM | Opcional/parcial |
| Crawler internacional profundo | Planejado |
| Browser scraping JS | Planejado/parcial |
| Taxonomy v4 / Smart Query Builder | Implementado |

## Desenvolvimento

- Rodar testes antes de commit.
- Não commitar `project_output/`.
- Não commitar PDFs grandes.
- Manter README fiel ao código.
- Atualizar `docs/REPO_AUDIT.md` quando houver remoções estruturais.
