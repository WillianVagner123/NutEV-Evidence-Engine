# NutEV Control Center

Painel local (Streamlit) para monitorar execução do pipeline, auditoria de claims e recomendações candidatas.

## Instalação
```bash
pip install -e ".[dashboard]"
```

## Execução
```bash
nutev dashboard --project-root ./project_output --port 8501
```
Abra: `http://localhost:8501`.

## Outputs lidos
- `02_metadata/metadata_master.csv`
- `02_metadata/NUTEV_EVIDENCE_CLAIMS.csv`
- `02_metadata/NUTEV_RECOMMENDATION_CANDIDATES.csv`
- `02_metadata/NUTEV_RECOMMENDATION_AUDIT_TRAIL.csv`
- `06_tables/NUTEV_GLOBAL_EVIDENCE_MATRIX.xlsx`
- `06_tables/NUTEV_PROTOCOL_TRANSLATION_MATRIX.xlsx`
- `06_tables/NUTEV_EVIDENCE_CLAIMS.xlsx`
- `06_tables/NUTEV_RECOMMENDATION_CANDIDATES.xlsx`
- `06_tables/NUTEV_HUMAN_REVIEW_QUEUE.xlsx`
- `07_logs/run_summary.json`
- `07_logs/run_events.jsonl`
- `08_docs/NUTEV_METHODS_MASTER.md`

## Interpretação
Cards de overview representam monitoramento, não aprovação automática.

## Uso na qualificação
Use as páginas Audit Engine, Recommendation Candidates e Human Review Queue para triagem e validação humana.

## Limitações
Sem persistência de edição no backend nesta versão.

## Evitar interpretações indevidas
O painel não gera recomendações novas e não substitui validação humana.

## Demo para qualificação
```bash
nutev demo-data --project-root ./project_output_demo
nutev dashboard --project-root ./project_output_demo --port 8501
```
Dados demo são simulados e não devem ser usados como evidência científica real.

## Revisão humana
O painel lê e registra decisões em `07_logs/human_review_decisions.csv` sem sobrescrever histórico.
A aprovação final depende de revisão humana explícita e vínculo documental.

## NutEV Platform API local
- Control Center (Streamlit): dashboard visual.
- NutEV Platform API (FastAPI): landing page + endpoints de leitura e registro controlado de revisão humana.
- Ambos leem os mesmos outputs e nenhum aprova recomendações finais automaticamente.

Rodar plataforma local:
```bash
pip install -e ".[platform]"
nutev serve --project-root ./project_output_demo --host 127.0.0.1 --port 8000
```
