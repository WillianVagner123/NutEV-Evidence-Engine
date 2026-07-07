from __future__ import annotations

"""Additional NutEV runtime hooks loaded automatically after sitecustomize."""

CKM_TERMS = [
    "cardiovascular-kidney-metabolic syndrome",
    "cardiovascular kidney metabolic syndrome",
    "cardiovascular-kidney-metabolic health",
    "cardiovascular kidney metabolic health",
    "cardiovascular-kidney-metabolic risk",
    "cardiovascular kidney metabolic risk",
    "cardio-kidney-metabolic syndrome",
    "cardio kidney metabolic syndrome",
    "cardiorenal metabolic syndrome",
    "ckm syndrome",
    "ckm health",
    "ckm risk",
]

CKM_BONUS_TERMS: tuple[tuple[str, float], ...] = tuple((term, 12.0) for term in CKM_TERMS)


def _extend_unique(existing: list[str], additions: list[str]) -> list[str]:
    seen = {str(item).lower() for item in existing}
    for item in additions:
        value = str(item).strip()
        if not value or value.lower() in seen:
            continue
        existing.append(value)
        seen.add(value.lower())
    return existing


def _patch_global_watch_ckm_terms() -> None:
    try:
        from nutev.global_watch import watch_query_builder as query_builder
        from nutev.global_watch import watch_scoring
    except Exception:
        return

    if not getattr(query_builder, "_nutev_ckm_terms_patched", False):
        context_terms = query_builder.CATEGORY_CONTEXT_TERMS.setdefault(
            "obesity_cardiometabolic",
            [],
        )
        _extend_unique(context_terms, CKM_TERMS)
        quick_groups = query_builder.QUICK_MODE_SEED_GROUPS.setdefault(
            "obesity_cardiometabolic",
            [],
        )
        if quick_groups:
            _extend_unique(quick_groups[min(1, len(quick_groups) - 1)], CKM_TERMS)
        else:
            quick_groups.append(list(CKM_TERMS))
        query_builder._nutev_ckm_terms_patched = True

    if not getattr(watch_scoring, "_nutev_ckm_terms_patched", False):
        watch_scoring.BONUS_TERMS = tuple(watch_scoring.BONUS_TERMS) + CKM_BONUS_TERMS
        watch_scoring.NUTMEV_SCOPE_TERMS = tuple(watch_scoring.NUTMEV_SCOPE_TERMS) + tuple(CKM_TERMS)
        watch_scoring._nutev_ckm_terms_patched = True


def _patch_final_querypack_terms() -> None:
    try:
        from nutev.querypacks import builders as builders_module
        from nutev.querypacks import provider_queries as provider_module
    except Exception:
        return

    original = getattr(provider_module, "render_queries_for_provider", None)
    if original is None or getattr(original, "_nutev_final_terms_patched", False):
        return

    def render_queries_for_provider_patched(keyword_taxonomy: dict, workstream: str, provider: str) -> list[str]:
        queries = list(original(keyword_taxonomy, workstream, provider))
        if provider == "pubmed":
            ws = builders_module.canonical_workstream(workstream)
            if ws == "busca2a":
                terms = [
                    "dietary approaches to stop hypertension",
                ]
            elif ws == "busca2b":
                terms = [
                    "non-alcoholic fatty liver disease",
                    "low carbohydrate diet",
                    "rapid review",
                ]
            else:
                terms = []
            queries.extend([f'"{term}"[Title/Abstract]' for term in terms])
        return builders_module.uniq([query for query in queries if query])

    render_queries_for_provider_patched._nutev_final_terms_patched = True  # type: ignore[attr-defined]
    provider_module.render_queries_for_provider = render_queries_for_provider_patched


_patch_global_watch_ckm_terms()
_patch_final_querypack_terms()
