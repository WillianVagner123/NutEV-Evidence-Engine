# NutEV Provider Settings

## 1. O que são
Configurações locais de provedores de LLM, busca e bases bibliográficas para a NutEV Platform/Control Center.

## 2. Como configurar API keys
Preferencialmente por variável de ambiente.

## 3. Por que preferir variáveis de ambiente
Evita armazenamento de segredo em arquivos locais e reduz risco de vazamento.

## 4. OpenAI
```bash
export OPENAI_API_KEY="..."
```
No Provider Settings, usar `env_var=OPENAI_API_KEY` e `secret_source=env`.

## 5. Ollama/local LLM
Configurar `base_url` (ex: `http://127.0.0.1:11434`) e `model`.

## 6. PubMed, Crossref e OpenAlex
- PubMed: `NCBI_API_KEY`/`NCBI_EMAIL`.
- Crossref: `CROSSREF_MAILTO`.
- OpenAlex: `OPENALEX_MAILTO`.

## 7. Segurança
- Arquivo local: `project_output/00_settings/provider_settings.local.json` (gitignored).
- API nunca retorna chaves completas (mascara).

## 8. Papel do LLM
Assistivo apenas.

## 9. O que o LLM não pode fazer
- Aprovar recomendação final.
- Substituir revisão humana.
- Fabricar evidência.

## 10. Uso na qualificação
Use Provider Settings para demonstrar governança local de integrações e rastreabilidade operacional.
