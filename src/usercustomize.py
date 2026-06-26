from __future__ import annotations

"""Additional NutEV runtime hooks loaded automatically after sitecustomize."""

GROUP_DELIVERY_TERMS = [
    "shared medical appointment",
    "shared medical appointments",
    "group medical visit",
    "group medical visits",
    "group visit",
    "group visits",
    "group-based lifestyle intervention",
    "group based lifestyle intervention",
    "group-based nutrition intervention",
    "group based nutrition intervention",
]

GROUP_DELIVERY_ANCHORS = [
    "obesity",
    "type 2 diabetes",
    "prediabetes",
    "cardiometabolic",
    "medical nutrition therapy",
    "nutrition",
    "diet",
    "lifestyle intervention",
]


def _or_block(terms: list[str], *, pubmed: bool = False) -> str:
    if pubmed:
        rendered = [f'"{term}"[Title/Abstract]' for term in terms]
    else:
        rendered = [f'"{term}"' for term in terms]
    return "(" + " OR ".join(rendered) + ")"


def _group_delivery_query(*, pubmed: bool = False) -> str:
    return " AND ".join(
        [
            _or_block(GROUP_DELIVERY_TERMS, pubmed=pubmed),
            _or_block(GROUP_DELIVERY_ANCHORS[:4], pubmed=pubmed),
            _or_block(GROUP_DELIVERY_ANCHORS[4:], pubmed=pubmed),
        ]
    )


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
                queries.append(_group_delivery_query(pubmed=True))
            else:
                terms = []
            queries.extend([f'"{term}"[Title/Abstract]' for term in terms])
        return builders_module.uniq([query for query in queries if query])

    render_queries_for_provider_patched._nutev_final_terms_patched = True  # type: ignore[attr-defined]
    provider_module.render_queries_for_provider = render_queries_for_provider_patched


def _patch_group_delivery_build_queries() -> None:
    try:
        from nutev.querypacks import builders as builders_module
    except Exception:
        return

    original = getattr(builders_module, "build_queries", None)
    if original is None or getattr(original, "_nutev_group_delivery_patched", False):
        return

    def build_queries_patched(keyword_taxonomy: dict, workstream: str) -> list[str]:
        queries = list(original(keyword_taxonomy, workstream))
        ws = builders_module.canonical_workstream(workstream)
        if ws == "busca2b":
            queries.append(_group_delivery_query())
        return builders_module.uniq([query for query in queries if query])

    build_queries_patched._nutev_group_delivery_patched = True  # type: ignore[attr-defined]
    builders_module.build_queries = build_queries_patched


_patch_final_querypack_terms()
_patch_group_delivery_build_queries()
