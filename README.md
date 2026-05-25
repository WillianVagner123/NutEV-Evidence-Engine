# NutEV/NutMEV — Evidence Engine for Lifestyle Nutrition

Pipeline computacional reprodutível para identificação, classificação, auditoria e tradução de evidências em recomendações candidatas para o Protocolo Dietético NutEV/NutMEV.

## Para rodar no PC

O guia principal está em:

- [`docs/RUN_LOCAL.md`](docs/RUN_LOCAL.md)

Caminho rápido:

```bash
git clone https://github.com/WillianVagner123/NUT-MEV_NEW.git
cd NUT-MEV_NEW
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dashboard,platform]"
nutev demo-data --project-root ./project_output_demo
nutev dashboard --project-root ./project_output_demo --port 8501
```

No Windows PowerShell, use:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dashboard,platform]"
nutev demo-data --project-root ./project_output_demo
nutev dashboard --project-root ./project_output_demo --port 8501
```

Depois acesse:

```text
http://127.0.0.1:8501
```

## Componentes principais

- NutEV Evidence Engine
- NutEV Audit Engine
- NutEV Scientific Rigor Layer
- NutEV Platform API
- NutEV Control Center
- Human Review and Adjudication
- Demo Data
- Global Watch

## Instalação

```bash
pip install -e ".[dashboard,platform]"
```

O projeto requer Python `>=3.12,<3.15`.

## Comandos principais

### Demo data

```bash
nutev demo-data --project-root ./project_output_demo
```

### Dashboard local

```bash
nutev dashboard --project-root ./project_output_demo --port 8501
```

### NutEV Platform API

```bash
nutev serve --project-root ./project_output_demo --host 127.0.0.1 --port 8000
```

URLs:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs

### NutEV Provider Settings

```bash
export OPENAI_API_KEY="..."
nutev serve --project-root ./project_output_demo --host 127.0.0.1 --port 8000
nutev dashboard --project-root ./project_output_demo --port 8501
```

As chaves são locais, devem ser preferencialmente resolvidas por variáveis de ambiente e não devem aparecer em outputs, logs, matrizes ou relatórios.

## Primeiro piloto real

```bash
nutev --project-root ./project_output_pilot --workstreams busca1 busca2a busca2b a3 --web-enabled
nutev pilot-report --project-root ./project_output_pilot
nutev dashboard --project-root ./project_output_pilot --port 8501
```

### Pipeline principal

```bash
nutev --project-root ./project_output --workstreams busca1 busca2a busca2b a3 --web-enabled
```

### Global Watch

```bash
nutev global-watch --project-root ./project_output --since-days 30 --mode thesis --web-enabled --official-crawl --country-discovery --capture-enabled
```

### Testes NutEV

```bash
PYTHONPATH=src python -m pytest -q tests/nutev
```

## Aviso metodológico

O sistema gera recomendações candidatas e matrizes de auditoria, mas **não substitui revisão humana**.

Uma RecommendationCandidate não é uma recomendação final. A entrada no Protocolo NutEV/NutMEV requer lastro documental, claim auditável, qualidade da evidência, ausência de conflito não adjudicado, validação humana e readiness compatível com protocolo.

## Demo para qualificação

Dados demo são simulados e servem para visualização e teste do fluxo operacional. Não devem ser usados como evidência científica real.

## Revisão humana

As decisões humanas são persistidas em `project_output/07_logs/human_review_decisions.csv` (append-only). Nenhuma recomendação deve ser considerada final sem revisão humana explícita e vínculo documental.

## Scientific Rigor Layer

A camada de rigor científico formaliza:

- modelo conceitual NutEV/NutMEV;
- qualidade da evidência;
- convergência entre lentes;
- registro de lacunas;
- dupla revisão humana e adjudicação;
- protocol readiness;
- bloqueio de inferências não validadas.

## Documentação

- `docs/RUN_LOCAL.md`
- `docs/NUTEV_AUDIT_ENGINE.md`
- `docs/NUTEV_CONTROL_CENTER.md`
- `docs/NUTEV_EVIDENCE_TO_PROTOCOL_FLOW.md`
- `docs/NUTEV_PLATFORM_API.md`
- `docs/NUTEV_PROVIDER_SETTINGS.md`
- `docs/REPOSITORY_STRUCTURE.md`
- `docs/LEGACY_CLEANUP_AUDIT.md`
- `docs/LEGACY_DEPENDENCY_MAP.md`

## Historical note

O repositório evoluiu de uma base histórica Local Deep Research. A arquitetura canônica atual para pesquisa e qualificação é NutEV/NutMEV (`src/nutev`).
