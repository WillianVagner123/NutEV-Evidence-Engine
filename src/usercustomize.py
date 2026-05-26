from __future__ import annotations

"""Additional NutEV runtime hooks loaded automatically after sitecustomize."""


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


_patch_final_querypack_terms()
