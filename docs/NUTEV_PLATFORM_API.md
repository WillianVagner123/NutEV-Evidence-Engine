# NutEV Platform API

## O que é
API local FastAPI para leitura dos outputs do NutEV e registro controlado de revisão humana.

## Diferença entre API, Control Center e pipeline
- Pipeline NutEV: processa evidências.
- Platform API: expõe resultados localmente via endpoints.
- Control Center: dashboard Streamlit para visualização/revisão.

## Instalação
```bash
pip install -e ".[platform]"
```

## Demo-data
```bash
nutev demo-data --project-root ./project_output_demo
```

## Iniciar servidor local
```bash
nutev serve --project-root ./project_output_demo --host 127.0.0.1 --port 8000
```

## Endpoints
- `GET /`
- `GET /api/health`
- `GET /api/run-summary`
- `GET /api/evidence`
- `GET /api/claims`
- `GET /api/recommendations`
- `GET /api/human-review-queue`
- `GET /api/human-review-decisions`
- `POST /api/human-review-decisions`
- `GET /api/artifacts`
- `GET /api/methods`

## Exemplos
```bash
curl http://127.0.0.1:8000/api/health
curl "http://127.0.0.1:8000/api/evidence?limit=20&offset=0"
curl http://127.0.0.1:8000/api/claims
```

## Segurança local
- Host default é `127.0.0.1`.
- Não expor publicamente sem autenticação.
- API não executa busca web automaticamente.
- API não gera recomendações finais.

## Limitações
- Sem autenticação/controle de acesso nesta fase.
- Operação local para uso controlado.

## Uso na qualificação
Use demo-data + API + Control Center para demonstrar fluxo reprodutível sem usar dados científicos reais como base de conclusão.

## Integração com piloto real
```bash
nutev --project-root ./project_output_pilot --workstreams busca1 busca2a busca2b a3 --web-enabled
nutev pilot-report --project-root ./project_output_pilot
```

## Provider endpoints
- `GET /api/providers`
- `GET /api/provider-settings`
- `POST /api/provider-settings`
- `POST /api/provider-settings/test`
- `GET /api/provider-health`
