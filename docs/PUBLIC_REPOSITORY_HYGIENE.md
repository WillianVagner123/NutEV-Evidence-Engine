# Public Repository Hygiene

This repository is now publicly presented as:

```text
NutEV/NutMEV — Evidence Engine for Lifestyle Nutrition
```

## Canonical public files

The GitHub tabs should now communicate the NutEV identity:

- `README.md` — NutEV/NutMEV overview and commands.
- `CONTRIBUTING.md` — NutEV contribution rules and scientific safeguards.
- `SECURITY.md` — NutEV security and data policy.
- `LICENSE` — MIT license.

## Legacy compatibility

The package still keeps some Local Deep Research compatibility because the repository evolved from that base. The package distribution name and some entry points remain compatible by design while the NutEV runtime becomes primary.

Canonical new work should target:

```text
src/nutev/
```

Legacy compatibility may remain under:

```text
src/local_deep_research/
```

## What not to do

- Do not add new doctorate logic into `src/local_deep_research/`.
- Do not commit real `project_output/` data.
- Do not expose API keys, `.env` files, or real patient/participant data.
- Do not present demo data as scientific evidence.

## Cleanup status

Completed:

- `CONTRIBUTING.md` aligned with NutEV/NutMEV.
- `pyproject.toml` includes NutEV/NutMEV description and compatibility notes.
- `README_old.md` replaced with a legacy pointer.
- Legacy archive index added at `archive/legacy_local_deep_research/README.md`.

Still intentionally retained:

- `src/local_deep_research/` compatibility source tree.
- legacy commands `ldr`, `ldr-web`, and `ldr-mcp`.
- selected legacy docs/scripts needed for compatibility or historical context.
