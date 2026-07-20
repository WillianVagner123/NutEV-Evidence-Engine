# Public Release Audit — NutEV/NutMEV

> Pre-change audit produced **before** any restructuring, as required by Etapa 1
> of the public-readiness plan. It is a read-only snapshot used to plan safe,
> incremental changes. No legacy code was moved or deleted to produce it.
>
> - Branch: `claude/nutev-public-readiness-3bg31o`
> - Method: `git ls-files`, `git count-objects -vH`, `git rev-list --objects --all`,
>   `git grep` for cross-imports and secret patterns, per-package import mapping.
> - Scope note: a fresh `gitleaks` scan could **not** be run in this environment
>   (binary unavailable). See §10.

## 1. Summarized repository tree

```
NutEV-Evidence-Engine/
├── src/
│   ├── nutev/                  # CANONICAL core (analysis, api, audit, cli, demo,
│   │                           #   download, engine, export, extract, global_watch,
│   │                           #   llm, pipelines, protocol, querypacks, review,
│   │                           #   search, ui)
│   ├── local_deep_research/    # LEGACY upstream engine (34 subpackages: web,
│   │                           #   database, benchmarks, news, research_library, …)
│   ├── sitecustomize.py        # legacy runtime shim
│   └── usercustomize.py        # legacy runtime shim
├── config/                     # CANONICAL NutEV JSON rule/ontology packs
├── nutev_tests/                # CANONICAL test suite (103 files)
├── tests/                      # LEGACY test suite (1905 files, 71 subdirs)
├── examples/                   # mixed (legacy report samples + api_usage/benchmarks)
├── docs/                       # mixed canonical NutEV docs + legacy LDR docs
├── requirements/               # nutev-ci.txt
├── scripts/                    # mixed
├── .github/workflows/          # 6 workflows (5 nutev-*, 1 web-frontend)
├── cookiecutter-docker/        # LEGACY docker scaffolding
├── unraid-templates/           # LEGACY deployment
├── docker-compose*.yml         # LEGACY (4 files) + Dockerfile
├── pyproject.toml, pdm.lock, package*.json
├── README.md, README_old.md    # README_old.md is the legacy LDR readme (35 KB)
└── LICENSE (MIT, LearningCircuit)
```

## 2. Total size

| Measure | Value |
|---|---|
| Working tree (`du -sh .`) | ~55 MB |
| Packed git history (`size-pack`) | 7.87 MiB |
| Tracked files (`git ls-files | wc -l`) | 3200 |
| Canonical test files (`nutev_tests/`) | 103 |
| Legacy test files (`tests/`) | 1905 |

## 3. 50 largest tracked files (top of the list)

Full list obtainable with `git ls-files -z | xargs -0 du -k | sort -rn | head -50`.
Notable entries (KB):

| Size (KB) | File | Class |
|---|---|---|
| 576 | `pdm.lock` | generated |
| 220 | `tests/database/backup/test_backup_service.py` | legacy test |
| 216 | `tests/database/test_alembic_migrations.py` | legacy test |
| 208 | `tests/news/test_base_subscription.py` | legacy test |
| 208 | `tests/database/test_sqlcipher_integration.py` | legacy test |
| 196 | `src/local_deep_research/web/static/js/components/settings.js` | legacy frontend |
| 172 | `src/local_deep_research/defaults/default_settings.json` | legacy generated/config |
| 164 | `tests/puppeteer/test_deep_functionality.js` | legacy test |
| 160 | `examples/detailed_report_how_to_improve_retrieval_augmented_generation…md` | legacy sample output |
| 156 | `tests/infrastructure_tests/package-lock.json` | generated |
| 132 | `src/local_deep_research/web/static/favicon.png` | legacy asset |
| 120 | `docs/CONFIGURATION.md` | legacy doc |

The single largest concentration of bytes is the **legacy** `tests/` tree, legacy
frontend JS, and generated lockfiles. None of the 50 largest tracked files belong
to `src/nutev`.

## 4. Largest objects in git history

`git rev-list --objects --all | git cat-file --batch-check … | sort -rn` returns the
same shape as §3 (history is dominated by `pdm.lock`, legacy test files, legacy
frontend JS, `default_settings.json`, and package-lock files). No unusually large
binary blob (media, dataset dump, PDF) was found in history — the largest blob is
`pdm.lock` at ~572 KB. History pack is only 7.87 MiB total, so no history rewrite is
warranted at this stage (and it is explicitly out of scope).

## 5. Canonical directories (NutEV core)

- `src/nutev/` — the canonical engine.
- `config/` — NutEV rule/ontology/scoring/taxonomy JSON packs (busca1/busca2a/busca2b).
- `nutev_tests/` — canonical test suite.
- `docs/NUTEV_*.md`, `docs/methodology`-class docs — canonical methodology.
- `examples/article1_pilot/` (to be created), `examples/minimal/` (to be created).

## 6. Legacy directories

- `src/local_deep_research/` — full upstream Local Deep Research engine (34 subpackages).
- `src/sitecustomize.py`, `src/usercustomize.py` — legacy runtime shims.
- `tests/` — 1905 legacy test files (71 subdirs).
- Legacy frontend: `src/local_deep_research/web/static`, `templates`.
- Legacy infra: `Dockerfile`, `docker-compose*.yml`, `cookiecutter-docker/`,
  `unraid-templates/`, `package.json`, `package-lock.json`.
- Legacy docs: `README_old.md`, and many `docs/*` (CONFIGURATION, SearXNG-Setup,
  SQLCIPHER_INSTALL, news, strategies, etc.).

## 7. Generated files

- `pdm.lock`, `package-lock.json`, `tests/**/package-lock.json` — lockfiles.
- `examples/*.md` sample research reports — generated LDR outputs.
- `src/local_deep_research/defaults/default_settings.json` — generated defaults.
- Any `project_output*/` — already git-ignored (runtime output).

## 8. Files potentially protected by copyright / third-party

- `examples/*.md` (e.g. `2008-finicial-crisis.md`, financial-crisis / spice-trade /
  fusion-energy reports) — LDR-generated narrative reports; provenance of quoted
  source text is unclear → treat as **review-before-publish**.
- `src/local_deep_research/**` — third-party project code (MIT, LearningCircuit).
- No third-party PDFs or full-text corpora are tracked (confirmed: no `.pdf` in the
  50 largest tracked files; runtime PDF capture dirs are git-ignored).

## 9. Possible personal data

- No patient/participant datasets are tracked.
- `.env.example` contains **empty** placeholders only (no real emails/keys).
- Workflow `env:` blocks reference `NCBI_EMAIL`, `CROSSREF_MAILTO`, `OPENALEX_MAILTO`
  via **GitHub secrets** (not committed values) — acceptable, but see §18.
- `README.md` contains `export NCBI_API_KEY="sua-chave-ncbi"` — a placeholder, not a
  real key.

## 10. Possible secrets

- `git grep -nE "(API_KEY|SECRET|TOKEN|PASSWORD|PRIVATE_KEY)"` returns only:
  (a) GitHub Actions `secrets.*` references in workflows (expected),
  (b) documentation and `.env.example` placeholders,
  (c) security-scanner scripts (`.github/scripts/file-whitelist-check.sh`).
  No hard-coded credential value was found in tracked source.
- `.gitleaksignore` **was reset** (2026-07): the previous 57 KB / 582-line baseline
  was inherited from the unrelated upstream project (`local_deep_research` /
  `web_search_engines`) — every fingerprint referenced a file/commit absent from this
  repository, so it suppressed nothing here while giving false assurance. It now holds
  no fingerprints (no known false positives for this repo); the gitleaks CI job scans
  clean against the current tree. Any future entry must be manually triaged as a
  confirmed non-secret before being added.
- `gitleaks` binary was unavailable in the audit environment; the fresh scan is
  deferred to the CI workflow added in Etapa 6.

## 11. Dependencies between `src/nutev` and `src/local_deep_research`

**`git grep -n "local_deep_research" src/nutev nutev_tests config` returns ZERO
matches.** The canonical core does **not** import the legacy package. This is the
single most important finding: it means version, entrypoint and dependency
decoupling (Etapas 2–3) are **safe** and can proceed without touching legacy code.

## 12. Cross-imports

- nutev → local_deep_research: **none** (see §11).
- local_deep_research → nutev: not required for the canonical install; legacy retains
  its own imports.
- Coupling that remains is only at the **packaging** layer:
  - `pyproject.toml` sources the version from `src/local_deep_research/__version__.py`;
  - `pyproject.toml` declares legacy entrypoints `ldr`, `ldr-web`, `ldr-mcp`;
  - `[project.dependencies]` mixes core + legacy-only heavy deps in one flat list.
  These three are addressed in Etapas 2–3.

## 13. Entrypoints

`[project.scripts]` currently declares: `ldr` (legacy), `ldr-web` (legacy),
`ldr-mcp` (legacy), `nutev` (canonical → `nutev.cli:main`). `nutev.cli` uses
lazy, per-command imports with graceful fallbacks (e.g. dashboard prints an install
hint if streamlit is missing), so it imports cleanly with only core deps.

## 14. Existing GitHub workflows

| Workflow | Purpose | Risk |
|---|---|---|
| `nutev-tests.yml` | canonical test matrix | `issue_comment` `/nutev-tests` trigger gated on body only, **not** author association → hardened in Etapa 6 |
| `nutev-lint.yml` | lint | low |
| `nutev-smoke.yml` | smoke | low |
| `nutev-full-once.yml` | full run (manual) | uploads **entire** `project_output` (raw captures/PDF/HTML) 14-day retention → sanitize in Etapa 6 |
| `nutev-global-watch.yml` | scheduled watch | uploads raw `09_global_watch` **and** `webhook_payload.json` unsanitized → fix in Etapa 6 |
| `web-frontend.yml` | legacy frontend | legacy; candidate to archive |

## 15. Current tests

- Canonical: `nutev_tests/` (103 files) — unit/contract/phase/global-watch groups.
  Runs green with the minimal core install (validated: see §19-style smoke below).
- Legacy: `tests/` (1905 files) — bound to `local_deep_research` (Flask, SQLCipher,
  puppeteer/playwright, news, research_library). Not part of canonical CI.
- Doc references alternate between `nutev_tests/` and `tests/nutev/`; the canonical
  location is standardized to **`nutev_tests/`** in Etapa 5.

## 16. Duplicated documentation

- `README.md` (canonical) vs `README_old.md` (legacy LDR readme, 35 KB).
- Legacy `docs/*` (CONFIGURATION, installation, install-pip, docker-compose-guide,
  SearXNG-Setup, news, strategies) overlap conceptually with canonical NutEV docs.
- Two existing legacy-audit docs already present: `docs/LEGACY_CLEANUP_AUDIT.md`,
  `docs/LEGACY_DEPENDENCY_MAP.md`.

## 17. Licenses and provenance

- Root `LICENSE`: **MIT, Copyright (c) 2025 LearningCircuit** — this attribution is
  the provenance of the inherited `local_deep_research` engine and **must be kept**.
- NutEV-specific contributions are additive on top of that base.
- No `NOTICE.md` yet → created in Etapa 7 to record inherited-vs-NutEV boundaries.
- Open legal question (logged as pending): confirm the exact upstream repository URL
  and whether any bundled asset (fonts, icons, sample reports) carries a different
  license.

## 18. Risks for public opening

1. `.gitleaksignore` (57 KB) not yet re-triaged (§10). **High-priority manual.**
2. Artifact uploads expose raw captures / `webhook_payload.json` (§14). **High.**
3. `issue_comment` CI trigger not author-gated (§14). **Medium.**
4. Legacy heavy deps installed for every user (Flask, FAISS, Elasticsearch,
   Playwright, SQLCipher, LangChain) (§12). **Medium (usability/attack surface).**
5. Generated LDR sample reports with unclear source provenance (§8). **Low–Medium.**
6. Version/identity still tied to legacy package (§12). **Low (fixed Etapa 2).**

## 19. Recommendation per group (keep / move / archive / rewrite / remove)

| Group | Recommendation | Notes |
|---|---|---|
| `src/nutev/` | **keep** | canonical core |
| `config/` | **keep** | canonical rule packs |
| `nutev_tests/` | **keep** | canonical tests |
| canonical `docs/NUTEV_*` | **keep** | methodology |
| `pyproject` version source | **rewrite** | point at `src/nutev/__version__.py` (Etapa 2) |
| `[project.scripts] ldr*` | **remove** from main / **move** to `legacy` extra (Etapa 2) |
| `[project.dependencies]` | **rewrite** | split core vs optional (Etapa 3) |
| `src/local_deep_research/` | **archive** (later) | keep in-tree until legacy tests/frontend are separated; do **not** move while packaging still ships it — sequence in `LEGACY_MIGRATION_PLAN.md` |
| `tests/` (legacy) | **archive** (later) | separate from canonical CI first |
| legacy frontend / Docker / cookiecutter / unraid | **archive** (later) | move to `legacy/` or history branch |
| `README_old.md` + legacy docs | **move** | to `docs/legacy/` |
| `examples/*.md` LDR reports | **review → archive/remove** | provenance unclear |
| `.gitleaksignore` | **rewrite** | re-triage (Etapa 6, manual) |
| artifact-uploading workflows | **rewrite** | sanitize (Etapa 6) |
| `web-frontend.yml` | **archive** | legacy |

---

**Bottom line:** the canonical core is already import-decoupled from legacy, so the
riskiest work (dependency and entrypoint separation) is safe. The legacy package must
**not** be moved or removed yet — it is still shipped by the current packaging and
still owns 1905 tests. Removal is sequenced in `docs/LEGACY_MIGRATION_PLAN.md`.
