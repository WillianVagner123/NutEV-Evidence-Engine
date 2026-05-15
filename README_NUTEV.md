# README_NUTEV

A documentação principal do NutMEV está em `README.md`.

Notas rápidas:
- Workstreams:
  - `PYTHONPATH=src python -m nutev.cli --project-root ./project_output --workstreams busca1 busca2a busca2b a3 --web-enabled`
- Global Watch:
  - `PYTHONPATH=src python -m nutev.cli global-watch --project-root ./project_output --since-days 7 --mode quick --web-enabled`
- Outputs: `project_output/`
- Auditoria: `docs/REPO_AUDIT.md`
- Limpeza/remoções: `docs/CLEANUP_REPORT.md`
