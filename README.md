# NutEV/NutMEV

A documentação operacional foi consolidada no `README.md` principal.

## Requisitos rápidos

- Python 3.12 ou superior (`pyproject.toml`: `>=3.12,<3.15`)
- Instalação editável recomendada: `pip install -e .`
- Após instalar, o atalho `nutev` fica disponível além de `python -m nutev.cli`

## Nota operacional

- O caminho canônico para coleta reprodutível do NutEV/NutMEV é o `nutev` CLI e os workflows GitHub Actions do repositório.
- O frontend web e o `docker-compose.yml` permanecem úteis como stack herdado da base `Local Deep Research`, mas não substituem o pipeline principal de evidências.

## Configuração rápida

1. Copie `.env.example` para `.env`.
2. Preencha apenas as chaves que você realmente vai usar.
3. Para debug offline/local, deixe `NUTEV_DISABLE_NETWORK=1` quando quiser garantir que nenhum provider externo seja chamado.

Variáveis comuns:
- `OPENAI_API_KEY`: opcional; se ausente, o pipeline pode registrar `llm_disabled` sem quebrar.
- `BRAVE_API_KEY`, `SERPAPI_API_KEY`, `GOOGLE_API_KEY`, `GOOGLE_CSE_ID`: opcionais; habilitam providers externos quando usados.
- `NUTEV_DIGEST_WEBHOOK_URL` e `NUTEV_NOTIFY_WEBHOOK`: opcionais; habilitam envio de resumo para webhook.

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
nutev --project-root ./project_output --workstreams busca1 busca2a busca2b a3 --web-enabled
```

Alternativa equivalente:

```bash
PYTHONPATH=src python -m nutev.cli --project-root ./project_output --workstreams busca1 busca2a busca2b a3 --web-enabled
```

## NutMEV Global Watch

Global Watch é vigilância contínua; workstreams (`busca1`, `busca2a`, `busca2b`, `a3`) continuam para execuções analíticas fechadas.

### Rodar local

```bash
nutev global-watch --project-root ./project_output --since-days 7 --mode quick
```

Alternativa equivalente:

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

## Webhook Dispatch

Use `--notify-webhook` para habilitar envio opcional de resumo JSON para webhook.
Configure `NUTEV_DIGEST_WEBHOOK_URL` e opcionalmente `NUTEV_NOTIFY_WEBHOOK=1`.
No GitHub, configure esses valores em **Secrets**.

Exemplo local:

```bash
nutev global-watch --project-root ./project_output --since-days 7 --mode thesis --web-enabled --capture-enabled --notify-webhook
```

Alternativa equivalente:

```bash
PYTHONPATH=src python -m nutev.cli global-watch --project-root ./project_output --since-days 7 --mode thesis --web-enabled --capture-enabled --notify-webhook
```

O payload envia resumo + links (não envia PDFs).
Se webhook ausente/falhar, o pipeline não quebra e registra evento.

### Capture layer (hardening)
- `--capture-enabled`: tenta capturar PDF/HTML público para top itens.
- `--capture-limit`: sobrescreve limite padrão (quick=10, thesis=30, exhaustive=100).
- status possíveis: `pdf`, `html_snapshot`, `metadata_only`.
- `--notify-webhook`: envia resumo opcional para webhook (sem anexar PDFs, apenas links e metadados).
