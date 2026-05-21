# Legacy Cleanup Audit (Local Deep Research → NutEV)

## Scope
Audit of inherited components to identify what is canonical NutEV, what is legacy, and what can be cleaned safely.

## 1) Clearly inherited from Local Deep Research
- `src/local_deep_research/` (full legacy app stack). **Recommendation:** `needs_manual_review` (large surface, referenced by non-NutEV tests and legacy scripts).
- `docs/*` pages centered on LDR web/search internals (e.g., analytics dashboard, CLI tools, architecture of LDR web). **Recommendation:** `move_to_legacy`.
- `docker-compose.yml`, Dockerfile stages for `ldr-web` legacy UI. **Recommendation:** `keep` for now (still operational for legacy users), later `move_to_legacy`.

## 2) Still used by NutEV
- `src/nutev/**` (Evidence/Audit/Control Center/demo/review/global watch). **Recommendation:** `keep`.
- `config/*` NutEV configs (`audit_rules`, ontology/lenses/source registry, scoring/taxonomy). **Recommendation:** `keep`.
- `tests/nutev/**`. **Recommendation:** `keep`.

## 3) Probably obsolete (NutEV scope)
- Legacy web/frontend docs not used by NutEV runtime. **Recommendation:** `move_to_legacy`.
- Legacy benchmarking/rate-limit references in docs. **Recommendation:** `move_to_legacy`.

## 4) Dangerous to remove without deeper analysis
- `src/local_deep_research/**` currently referenced by many repository tests and entrypoints (`ldr`, `ldr-web`, `ldr-mcp`). **Recommendation:** `needs_manual_review`.
- `.github/workflows/web-frontend.yml` and legacy JS infra tests. **Recommendation:** `needs_manual_review`.

## 5) Dependencies linked mainly to legacy
- Flask/websocket/auth stack and large LDR ecosystem dependencies in `pyproject.toml` likely primarily legacy.
- **Recommendation:** `needs_manual_review` with staged dependency-pruning plan after isolating NutEV package profile.

## 6) Old scripts likely unused by NutEV runtime
- Legacy dev scripts under docs/developing and LDR helper scripts. **Recommendation:** `move_to_legacy` or keep documented as historical.

## 7) Old frontend/web
- Root Vite/frontend and `src/local_deep_research/web/**` are legacy-facing. **Recommendation:** `needs_manual_review`.

## 8) Old docker-compose stack
- Legacy stack still documents LDR services/network (`ldr-network`). **Recommendation:** `keep` short term, tag as historical/legacy.

## 9) Textual references to Local Deep Research
- Present across many docs and CI templates. **Recommendation:** reduce in top-level README, consolidate historical note, map legacy docs.

## 10) Item-level recommendation matrix
- `src/nutev/**`: **keep**
- `tests/nutev/**`: **keep**
- `src/local_deep_research/**`: **needs_manual_review**
- legacy LDR docs: **move_to_legacy**
- legacy docker/web workflow files: **needs_manual_review**
