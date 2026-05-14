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
