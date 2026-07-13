# Dependency Architecture

NutEV/NutMEV is split into a **small mandatory core** and a set of **optional
extras**, so that a basic bibliographic run does not pull the entire legacy
stack (Flask, frontend, Elasticsearch, FAISS, Playwright, SQLCipher, LangChain).

## Design principles

1. A basic bibliographic search must install and run with the smallest possible
   dependency set.
2. AI/LLM dependencies are **optional** — NutEV runs without any LLM.
3. Google, SerpAPI and Brave are **optional** — scientific search works without them.
4. Heavy/system-coupled dependencies (OCR, browsers, DB encryption) are optional.
5. There is a minimal **CI profile** (`requirements/nutev-ci.txt`).
6. No duplicated declarations of the same responsibility across core groups.
7. Every core dependency has a documented reason (below).

## Core (`[project.dependencies]`)

Installed by `pip install -e .`. Enough for `nutev demo-data`, config parsing,
basic search and tabular I/O.

| Package | Why it is core |
|---|---|
| `pandas` | Tabular pipelines, exports, demo data — used across analysis, export, audit, protocol, review, pipelines. |
| `pydantic` | Typed engine/audit/api models. |
| `requests` | HTTP client for bibliographic search and public downloads. |
| `beautifulsoup4` | HTML parsing in search/global_watch/download. |
| `python-dateutil` | Robust parsing of publication dates. |
| `openpyxl` | `.xlsx` export tables (export/extract). |
| `typing-extensions` | Typing backports used across the core. |

Mirror file: `requirements/nutev-core.txt`.

## Optional extras (`[project.optional-dependencies]`)

| Extra | Install | Purpose | Notable deps |
|---|---|---|---|
| `search` | `.[search]` | Extra search providers | `arxiv`, `wikipedia`, `google-search-results` (SerpAPI, optional), `lxml`, `xmltodict` |
| `documents` | `.[documents]` | PDF/DOCX/OCR extraction (needs system `tesseract`, `poppler`) | `pypdf`, `pdfplumber`, `pdf2image`, `pytesseract`, `python-docx`, `Pillow` |
| `dashboard` | `.[dashboard]` | Streamlit review dashboard | `streamlit`, `plotly` |
| `api` | `.[api]` | FastAPI REST platform | `fastapi`, `uvicorn`, `jinja2` |
| `platform` | `.[platform]` | Alias of `api` (kept for the CLI hint) | → `api` |
| `llm` | `.[llm]` | Optional LLM providers | `langchain*`, `tiktoken` |
| `watch` | `.[watch]` | Global Watch browser capture + scheduling | `playwright`, `apscheduler`, `aiohttp`, `tenacity` |
| `mcp` | `.[mcp]` | MCP server | `mcp[cli]` |
| `dev` | `.[dev]` | Test/lint/type tooling | `pytest*`, `ruff`, `mypy`, `hypothesis`, … |
| `legacy` | `.[legacy]` | Full inherited `local_deep_research` stack | Flask, SQLCipher, Elasticsearch, FAISS, LangChain, … |
| `all` | `.[all]` | Everything above (incl. legacy) | recursive extra |

### Execution guarantees

- **Without any LLM:** core only; `llm_enabled` stays off. The LLM assists but
  never approves a recommendation.
- **Without Google/SerpAPI/Brave:** core + (optionally) `search`; provider keys
  are read from env and simply skipped when absent.
- **Demo without any key or network:** `pip install -e ".[dashboard]"` →
  `nutev demo-data` → `nutev dashboard`.

## CI profile

`requirements/nutev-ci.txt` is the minimal set the canonical tests import. The
default PR CI installs it (never the full/legacy stack) so PRs do not pull
Flask/FAISS/Elasticsearch/Playwright/SQLCipher.

## Legacy coupling

- The `local_deep_research` engine requires the `legacy` extra. It is **not**
  installed by the main distribution and the NutEV core never imports it
  (verified: `git grep local_deep_research src/nutev` → no matches).
- Removal of the legacy package from the wheel is sequenced in
  `docs/LEGACY_MIGRATION_PLAN.md`.

## Known follow-ups (pending)

- `pdm.lock` still reflects the pre-split flat dependency list and should be
  regenerated (`pdm lock`) in a dedicated PR. `pip install -e .` does **not**
  use the lock, so the acceptance path is unaffected.
- Consider pinning a resolved constraints file for reproducible CORE installs.
