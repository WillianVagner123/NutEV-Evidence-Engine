from __future__ import annotations

"""Additional NutEV runtime hooks loaded automatically after sitecustomize."""

_ADIPOSITY_CLINICAL_TERMS = [
    "adiposity-based chronic disease",
    "adiposity based chronic disease",
]


def _extend_unique(target: list[str], terms: list[str]) -> None:
    seen = {str(item).strip().lower() for item in target if str(item).strip()}
    for term in terms:
        clean = str(term).strip()
        if not clean:
            continue
        lower = clean.lower()
        if lower in seen:
            continue
        target.append(clean)
        seen.add(lower)


def _patch_adiposity_query_terms() -> None:
    try:
        from nutev.querypacks import builders as builders_module
        from nutev.querypacks import provider_queries as provider_module
    except Exception:
        return

    for workstream in ("busca2a", "busca2b"):
        enhancements = builders_module.WORKSTREAM_QUERY_ENHANCEMENTS.get(workstream, {})
        _extend_unique(
            enhancements.setdefault("condition_terms", []),
            _ADIPOSITY_CLINICAL_TERMS,
        )

    original = getattr(provider_module, "render_queries_for_provider", None)
    if original is None or getattr(original, "_nutev_final_terms_patched", False):
        return

    def render_queries_for_provider_patched(
        keyword_taxonomy: dict,
        workstream: str,
        provider: str,
    ) -> list[str]:
        queries = list(original(keyword_taxonomy, workstream, provider))
        if provider == "pubmed":
            ws = builders_module.canonical_workstream(workstream)
            if ws == "busca2a":
                terms = [
                    "dietary approaches to stop hypertension",
                    *_ADIPOSITY_CLINICAL_TERMS,
                ]
            elif ws == "busca2b":
                terms = [
                    "non-alcoholic fatty liver disease",
                    "low carbohydrate diet",
                    "rapid review",
                    *_ADIPOSITY_CLINICAL_TERMS,
                ]
            else:
                terms = []
            queries.extend([f'"{term}"[Title/Abstract]' for term in terms])
        return builders_module.uniq([query for query in queries if query])

    render_queries_for_provider_patched._nutev_final_terms_patched = True  # type: ignore[attr-defined]
    provider_module.render_queries_for_provider = render_queries_for_provider_patched


def _patch_adiposity_watch_terms() -> None:
    try:
        from nutev.global_watch import watch_config as watch_config_module
        from nutev.global_watch import watch_scoring as watch_scoring_module
    except Exception:
        return

    _extend_unique(
        watch_config_module.WATCH_CATEGORIES.setdefault("obesity_cardiometabolic", []),
        _ADIPOSITY_CLINICAL_TERMS,
    )

    original = getattr(watch_scoring_module, "score_watch_item", None)
    if original is None or getattr(original, "_nutev_adiposity_terms_patched", False):
        return

    def score_watch_item_patched(item: dict) -> float:
        score = float(original(item))
        text = watch_scoring_module._build_scoring_text(item)
        if any(term in text for term in _ADIPOSITY_CLINICAL_TERMS):
            score += 12
        return round(score, 3)

    score_watch_item_patched._nutev_adiposity_terms_patched = True  # type: ignore[attr-defined]
    watch_scoring_module.score_watch_item = score_watch_item_patched


def _patch_adiposity_curated_priority() -> None:
    try:
        from nutev.export import curation as curation_module
    except Exception:
        return

    _extend_unique(curation_module._PRIORITY_TERMS, _ADIPOSITY_CLINICAL_TERMS)


_patch_adiposity_query_terms()
_patch_adiposity_watch_terms()
_patch_adiposity_curated_priority()
