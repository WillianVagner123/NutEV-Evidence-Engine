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

## Reporting
If you find a security issue, open a private report to repository maintainers instead of public disclosure with exploit details.
