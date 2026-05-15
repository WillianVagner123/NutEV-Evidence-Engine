# REPO_AUDIT

## 1. Estrutura encontrada
- Código NutMEV principal em `src/nutev/` (engine, global_watch, pipelines, search, download, extract, analysis, export, querypacks).
- Workflows em `.github/workflows/` (`nutev-global-watch.yml`, `nutev-tests.yml`, `nutev-lint.yml`, `nutev-smoke.yml`).
- Configs de domínio e taxonomia em `config/`.
- Testes em `nutev_tests/`.
- Há conteúdo herdado do projeto-mãe em `src/local_deep_research/`, `docs/` amplos e `examples/`.
- Há diretórios de backup versionados (`backup_*`), `node_modules/` e outputs em `project_output/`.

## 2. Módulos usados
- **USADO / MANTER**: `src/nutev/engine`, `src/nutev/global_watch`, `src/nutev/pipelines`, `src/nutev/search`, `src/nutev/download`, `src/nutev/extract`, `src/nutev/analysis`, `src/nutev/export`, `src/nutev/querypacks`.

## 3. Módulos possivelmente legados
- `src/local_deep_research/*` (mantido por segurança nesta fase).
- Parte de `docs/*` e `examples/*` aparenta ser legado do projeto-mãe.
- `node_modules/` na raiz e em subpastas de testes aparenta artefato de ambiente.

## 4. Workflows usados
- `.github/workflows/nutev-global-watch.yml` (watch semanal/manual, testes + artifacts).
- `.github/workflows/nutev-tests.yml` (testes).
- `.github/workflows/nutev-lint.yml` (lint).
- `.github/workflows/nutev-smoke.yml` (smoke).

## 5. Workflows possivelmente legados
- Nenhum removido nesta fase; todos mantidos por segurança.

## 6. Arquivos de configuração usados
- `config/keyword_taxonomy.json`
- `config/domain_rules_busca1.json`
- `config/domain_rules_busca2a.json`
- `config/domain_rules_busca2b.json`
- `config/scoring_rules.json`
- `config/official_sources_manifest.json`
- `config/official_sources_manifest_expanded.json`
- `config/global_watch_sources.json`

## 7. Arquivos que NÃO devem ser removidos
- Todos os módulos em `src/nutev/*`.
- `config/*.json` relacionados aos workstreams e global watch.
- `nutev_tests/*`.
- `.github/workflows/nutev-global-watch.yml`.
- `README.md` e `README_NUTEV.md`.

## 8. Arquivos candidatos à limpeza futura
- `backup_*` versionados.
- `node_modules/` versionado na raiz.
- caches Python versionados (`__pycache__/`).
- possivelmente docs/examples herdados do projeto-mãe, mediante revisão por impacto.

## 9. Riscos de remoção
- Remover `src/local_deep_research` ou docs/workflows herdados sem análise pode quebrar jobs de CI ou dependências indiretas.
- Remover configs pode quebrar geração de querypacks e scoring.
- Remover testes antigos pode esconder regressões.

## 10. Comandos de validação
- `PYTHONPATH=src python -m pytest -q nutev_tests -p no:timeout`
- `PYTHONPATH=src python -m nutev.cli --project-root ./project_output --workstreams busca1 busca2a busca2b a3 --web-enabled`
- `PYTHONPATH=src python -m nutev.cli global-watch --project-root ./project_output --since-days 7 --mode quick --web-enabled`
- `PYTHONPATH=src python -m nutev.cli global-watch --project-root ./project_output --since-days 7 --mode quick --web-enabled --capture-enabled --capture-limit 5`
