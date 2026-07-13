# Legacy Migration Plan

How the inherited `local_deep_research` (LDR) engine is progressively isolated
and eventually removed from the main NutEV/NutMEV distribution — **without**
breaking the `nutev` command at any step.

## Guardrails

- Do **not** move or delete legacy code until: dependencies are mapped, tests
  run, dependents are documented, a migration plan exists, and `nutev` still
  works. (This document is that plan; the audit is `docs/PUBLIC_RELEASE_AUDIT.md`.)
- No history rewrite / `git filter-repo` / `git push --force` in this phase.
- Each step is a **small, separate PR**.

## Current state (baseline)

- `src/nutev` imports `local_deep_research`: **none** (verified).
- Coupling is only at the packaging layer, and steps 1–3 below are **already
  done** on this branch:
  - [x] Version decoupled → `src/nutev/__version__.py`.
  - [x] Entrypoints decoupled → only `nutev` remains; `ldr*` removed from main.
  - [x] Dependencies split → legacy stack moved to the `legacy` extra.
- Still shipped in-tree: `src/local_deep_research/**`, legacy `tests/` (1905
  files), legacy frontend/Docker/cookiecutter/unraid, `README_old.md`.

## PR sequence

| # | PR | Scope | Risk | Blocking condition |
|---|---|---|---|---|
| 1 | `build: decouple nutev version from legacy package` | version source → nutev | low | **done** |
| 2 | `build: remove legacy console scripts from main install` | drop `ldr*` scripts | low | **done** |
| 3 | `build: split core and optional dependencies` | legacy deps → `legacy` extra | med | **done** |
| 4 | `refactor: remove cross-imports (if any appear)` | keep nutev free of LDR imports; add CI guard `git grep local_deep_research src/nutev` must be empty | low | none |
| 5 | `test: separate legacy tests from canonical CI` | canonical CI runs only `nutev_tests/`; legacy `tests/` excluded from default runs | low | canonical suite green |
| 6 | `docs: move legacy docs to docs/legacy/` | `README_old.md` + legacy `docs/*` → `docs/legacy/` | low | link check |
| 7 | `chore: move legacy frontend + Docker to legacy/` | frontend/`Dockerfile`/`docker-compose*`/`cookiecutter-docker`/`unraid-templates` → `legacy/` | med | confirm nothing canonical imports them |
| 8 | Decide legacy destination | (a) `legacy/` folder, (b) separate repo, or (c) history branch `legacy/local-deep-research` | — | maintainer decision (see below) |
| 9 | `build: drop local_deep_research from the wheel` | exclude legacy package + its `[tool.setuptools.package-data]` from the built distribution; keep in `legacy` extra only if still needed | med | steps 5–8 complete, `nutev` install still works |

## Step 8 — where legacy goes (decision pending, maintainer)

| Option | Pros | Cons |
|---|---|---|
| `legacy/` folder in-repo | simple; discoverable; no history change | keeps repo large |
| Separate repo | clean split; smaller main repo | loses inline history unless mirrored |
| History branch only | smallest main branch | harder to discover; still in history |

Recommended default: **`legacy/` folder now** (cheap, reversible), with an
explicit `legacy/README.md` pointing to provenance (`NOTICE.md`) and stating the
package is unsupported for scientific use. Repo/branch extraction can follow
later if size becomes a problem — and it is a history rewrite, out of scope here.

## Acceptance for "legacy removed from main distribution"

- `pip install -e .` in a clean env installs **no** legacy dependency.
- `nutev demo-data` / `nutev dashboard` work without the legacy extra.
- Canonical `nutev_tests/` pass without `local_deep_research` installed.
- The legacy engine remains reproducible via `pip install -e ".[legacy]"`.
- Provenance/licensing preserved (`LICENSE`, `NOTICE.md`).

## Do NOT do yet

- Delete `src/local_deep_research/**` or legacy `tests/` (still referenced by
  packaging/tests until steps 5, 9).
- Rewrite git history.
