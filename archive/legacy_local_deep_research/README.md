# Legacy Local Deep Research archive

This folder documents historical Local Deep Research material that still exists in the repository for compatibility while NutEV/NutMEV becomes the canonical doctorate platform.

## Current status

The canonical runtime for new work is:

```text
src/nutev/
```

The historical Local Deep Research runtime may still exist under:

```text
src/local_deep_research/
```

Do not use legacy modules for new NutEV doctorate work unless explicitly justified.

## Why legacy material remains

The repository evolved from a Local Deep Research base. Some legacy code, scripts, templates, and package metadata are retained temporarily because removing them in one step could break compatibility or tests.

## Public-facing identity

The public-facing project identity is now:

```text
NutEV/NutMEV — Evidence Engine for Lifestyle Nutrition
```

## Migration guidance

Prefer these commands:

```bash
nutev demo-data --project-root ./project_output_demo
nutev serve --project-root ./project_output_demo --host 127.0.0.1 --port 8000
nutev dashboard --project-root ./project_output_demo --port 8501
PYTHONPATH=src python -m pytest -q tests/nutev
```

Legacy commands such as `ldr`, `ldr-web`, and `ldr-mcp` are retained only for compatibility during the transition.

## Cleanup roadmap

1. Keep `src/nutev/` as the canonical runtime.
2. Avoid new dependencies from NutEV into `src/local_deep_research/`.
3. Move or summarize historical docs in this archive.
4. Split legacy CI/tests from NutEV CI before aggressive removal.
5. Remove compatibility entry points only after confirming they are no longer needed.
