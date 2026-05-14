# NutEV/NutMEV

A documentação operacional foi consolidada no `README.md` principal.

## Arquitetura canônica NutMEV

A Fase 0 introduz uma camada central para robustez e reprodutibilidade:

- **SearchCase**: contrato da intenção da execução (workstreams, modo, flags, configuração).
- **SearchJob**: contrato da execução concreta com `run_id`, status e snapshot imutável.
- **EvidenceArtifact**: PDFs/HTML/TXT/JSON/screenshot passam a ser artefatos rastreáveis, não a verdade canônica.
- **Metadata Master**: `metadata_master.csv` é a fonte de verdade para síntese e auditoria.
- **Run Events**: eventos estruturados JSONL para observabilidade e troubleshooting.
- **Artifact Manifest**: inventário com hash SHA256, tamanho, estágio e status de cada artefato.

### Por que isso importa para reprodutibilidade

1. Congela contexto de execução (config, args, versão, commit).
2. Mantém rastreabilidade ponta-a-ponta (candidate → download → extraction → synthesis).
3. Evita perda de evidência com fallback `metadata_only` em falhas de download/captura.
4. Prepara base para NutMEV Global Watch e automação via GitHub Actions.

Use:

```bash
PYTHONPATH=src python -m nutev.cli --project-root ./project_output --workstreams busca1 busca2a busca2b a3 --web-enabled
```

## NutMEV Global Watch

Global Watch é vigilância contínua; workstreams (`busca1`, `busca2a`, `busca2b`, `a3`) continuam para execuções analíticas fechadas.

### Rodar local

```bash
PYTHONPATH=src python -m nutev.cli global-watch --project-root ./project_output --since-days 7 --mode quick
```

### Rodar no GitHub Actions
Workflow: `.github/workflows/nutev-global-watch.yml` (manual e semanal domingo 10:00 UTC).

### Outputs
- `project_output/09_global_watch/global_watch_master.csv`
- `project_output/09_global_watch/runs/YYYY-MM-DD/global_watch_digest.md`
- `project_output/08_docs/NUTEV_GLOBAL_WATCH_LATEST.md`

### OPENAI_API_KEY
Se ausente, o pipeline não quebra e registra `llm_disabled`.

### Limitações
Falhas 403/400/404, paywall, CAPTCHA e APIs indisponíveis geram `metadata_only`/`failure_reason`, sem derrubar a execução.
