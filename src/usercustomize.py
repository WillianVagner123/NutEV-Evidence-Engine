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


def _patch_bariatric_surgery_noise() -> None:
    try:
        from nutev.analysis import relevance as relevance_module
    except Exception:
        return

    out_of_scope_domains = getattr(relevance_module, "OUT_OF_SCOPE_DOMAINS", None)
    negative_rules = getattr(relevance_module, "NEGATIVE_TITLE_RULES", None)
    if not isinstance(out_of_scope_domains, dict) or not isinstance(negative_rules, dict):
        return

    out_of_scope_domains.setdefault(
        "bariatric_or_metabolic_surgery",
        {
            "tokens": [
                "bariatric surgery",
                "metabolic surgery",
                "bariatric surgical",
                "metabolic surgical",
                "sleeve gastrectomy",
                "gastric bypass",
                "roux-en-y",
                "roux en y",
            ],
            "penalty": -10,
        },
    )
    negative_rules.update(
        {
            "bariatric surgery": -8,
            "metabolic surgery": -8,
            "sleeve gastrectomy": -8,
            "gastric bypass": -8,
        }
    )


_patch_final_querypack_terms()
_patch_bariatric_surgery_noise()
