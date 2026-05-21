# Legacy Dependency Map

## Method
- Searched repository for: `local_deep_research`, `advanced_search_system`, `frontend`, `ldr-web`, `docker-compose`.
- Reviewed NutEV runtime imports (`src/nutev/**`) and CLI entrypoints.

## Mapping (runtime focus)
| Module / Area | Imported by | Runtime for NutEV? | In tests? | Action |
|---|---|---:|---:|---|
| `src/nutev/**` | `nutev.cli` and NutEV tests | Yes | Yes | keep |
| `src/local_deep_research/**` | legacy entrypoints (`ldr*`) and legacy tests | No (NutEV core) | Yes (non-NutEV tests) | needs_manual_review |
| `streamlit` | `src/nutev/ui/dashboard.py` | Optional (dashboard) | Indirect | keep (optional extra) |
| Legacy web/frontend assets | legacy workflows/tests/docs | No (NutEV core) | Yes | needs_manual_review |
| Docker legacy stack (`docker-compose.yml`) | operators/docs | No (NutEV core) | N/A | keep short-term, mark legacy |

## NutEV dependency on legacy modules
- Direct imports from `src/nutev/**` to `local_deep_research` were audited; no direct runtime dependency is intended.
- CLI `nutev` now routes only through `src/nutev` modules for pipeline, demo-data and dashboard.

## Recommendation
1. Keep legacy modules in-place for now to avoid breaking non-NutEV tests/workflows.
2. Introduce gradual archival plan (`archive/legacy_local_deep_research/`) once CI/profile split is agreed.
3. Maintain explicit tests ensuring NutEV runtime path does not import legacy namespace.
