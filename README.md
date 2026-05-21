# NutEV/NutMEV — Evidence Engine for Lifestyle Nutrition

Pipeline computacional reprodutível para identificação, classificação, auditoria e tradução de evidências em recomendações candidatas para o Protocolo Dietético NutEV.

## Componentes principais
- NutEV Evidence Engine
- NutEV Audit Engine
- NutEV Control Center
- Human Review
- Demo Data
- Global Watch

## Instalação
```bash
pip install -e ".[dashboard,platform]"
```

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
pip install -e ".[platform]"
nutev demo-data --project-root ./project_output_demo
nutev serve --project-root ./project_output_demo --port 8000
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
As chaves são locais e não devem aparecer em outputs/reports.

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

## Demo para qualificação
Dados demo são simulados e servem para visualização e teste do fluxo operacional. Não devem ser usados como evidência científica real.

## Revisão humana
As decisões humanas são persistidas em `project_output/07_logs/human_review_decisions.csv` (append-only). Nenhuma recomendação deve ser considerada final sem revisão humana explícita e vínculo documental.

## Documentação
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
