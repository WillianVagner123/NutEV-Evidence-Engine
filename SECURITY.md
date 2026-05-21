# Security Policy (NutEV/NutMEV)

## Secret handling
- Never commit API keys, tokens, credentials, or `.env` files.
- Use environment variables via local `.env` (ignored by git).
- Keep `.env.example` free of real secrets.

## Data policy
- `project_output/` and local generated artifacts should not be committed (except intentional demo fixtures).
- Demo datasets must be clearly marked (`is_demo_data=true`) and are not scientific evidence.

## Public repository hygiene
- Review logs/artifacts before commit to avoid leaking sensitive data.
- Avoid committing large generated outputs with potentially sensitive content.
- A API NutEV Platform roda localmente por padrão em `127.0.0.1`.
- Não exponha a API em servidor público sem autenticação e controles adicionais.
- Endpoints da API não executam busca web automaticamente.
- Endpoints da API não geram recomendações finais.

## Reporting
If you find a security issue, open a private report to repository maintainers instead of public disclosure with exploit details.

## Provider Settings e secrets
- Preferir `secret_source=env` para API keys.
- Não exibir API key completa no frontend/API (apenas mascarada).
- Não gravar chaves em `docs/`, `config/`, `02_metadata/`, `06_tables/`, `07_logs/`, `08_docs/`.
- Endpoints da Platform API não aprovam recomendações finais e não executam síntese automática.
