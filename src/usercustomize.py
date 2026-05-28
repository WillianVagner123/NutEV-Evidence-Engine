from __future__ import annotations

"""Additional NutEV runtime hooks loaded automatically after sitecustomize."""

CHRONONUTRITION_TERMS = [
    "chrononutrition",
    "chrono-nutrition",
    "meal timing",
    "time-restricted feeding",
    "time restricted feeding",
    "early time-restricted eating",
    "early time restricted eating",
]

_CHRONONUTRITION_CONDITION_QUERY = (
    '("obesity" OR "prediabetes" OR "insulin resistance" OR '
    '"cardiometabolic risk" OR "metabolic syndrome" OR "MASLD" OR "NAFLD")'
)

_CHRONONUTRITION_EVIDENCE_QUERY = (
    '("randomized controlled trial" OR "systematic review" OR '
    '"umbrella review" OR "network meta-analysis" OR "implementation study")'
)

_CHRONONUTRITION_IMPLEMENTATION_QUERY = (
    '("adherence" OR "implementation" OR "behavior change" OR '
    '"glycemic control" OR "weight management")'
)


def _extend_unique_terms(target: list[str], additions: list[str]) -> list[str]:
    seen = {str(item).strip().lower() for item in target if str(item).strip()}
    for term in additions:
        clean = str(term).strip()
        lowered = clean.lower()
        if clean and lowered not in seen:
            target.append(clean)
            seen.add(lowered)
    return target


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
                    *CHRONONUTRITION_TERMS,
                ]
            else:
                terms = []
            queries.extend([f'"{term}"[Title/Abstract]' for term in terms])
        return builders_module.uniq([query for query in queries if query])

    render_queries_for_provider_patched._nutev_final_terms_patched = True  # type: ignore[attr-defined]
    provider_module.render_queries_for_provider = render_queries_for_provider_patched


def _patch_query_builder_chrononutrition() -> None:
    try:
        from nutev.querypacks import builders as builders_module
    except Exception:
        return

    original = getattr(builders_module, "build_queries", None)
    if original is None or getattr(original, "_nutev_chrononutrition_patched", False):
        return

    chrono_clause = builders_module.search_or_block(CHRONONUTRITION_TERMS)
    if not chrono_clause:
        return

    def build_queries_patched(keyword_taxonomy: dict, workstream: str) -> list[str]:
        queries = list(original(keyword_taxonomy, workstream))
        if builders_module.canonical_workstream(workstream) == "busca2b":
            queries.append(
                f"{chrono_clause} AND {_CHRONONUTRITION_CONDITION_QUERY} AND {_CHRONONUTRITION_EVIDENCE_QUERY}"
            )
            queries.append(
                f"{chrono_clause} AND {_CHRONONUTRITION_CONDITION_QUERY} AND {_CHRONONUTRITION_IMPLEMENTATION_QUERY}"
            )
        return builders_module.uniq([query for query in queries if query])

    build_queries_patched._nutev_chrononutrition_patched = True  # type: ignore[attr-defined]
    builders_module.build_queries = build_queries_patched


def _patch_global_watch_chrononutrition() -> None:
    try:
        from nutev.global_watch import watch_config as watch_config_module
        from nutev.global_watch import watch_query_builder as watch_query_builder_module
        from nutev.global_watch import watch_scoring as watch_scoring_module
    except Exception:
        return

    watch_terms = CHRONONUTRITION_TERMS + ["circadian eating"]
    _extend_unique_terms(
        watch_config_module.WATCH_CATEGORIES.setdefault("diet_patterns", []),
        watch_terms,
    )
    _extend_unique_terms(
        watch_query_builder_module.CATEGORY_CONTEXT_TERMS.setdefault("diet_patterns", []),
        watch_terms,
    )
    diet_pattern_seeds = watch_query_builder_module.QUICK_MODE_SEED_GROUPS.setdefault(
        "diet_patterns",
        [],
    )
    if diet_pattern_seeds:
        _extend_unique_terms(diet_pattern_seeds[-1], watch_terms)

    original = getattr(watch_scoring_module, "score_watch_item", None)
    if original is None or getattr(original, "_nutev_chrononutrition_patched", False):
        return

    def score_watch_item_patched(item: dict) -> float:
        score = float(original(item))
        text = " ".join(
            str(item.get(field, "") or "")
            for field in ("title", "abstract", "snippet", "evidence_type", "category")
        ).lower()
        if any(term in text for term in CHRONONUTRITION_TERMS):
            score += 14
        if "early time-restricted eating" in text or "time-restricted feeding" in text:
            score += 4
        return round(score, 3)

    score_watch_item_patched._nutev_chrononutrition_patched = True  # type: ignore[attr-defined]
    watch_scoring_module.score_watch_item = score_watch_item_patched


def _patch_relevance_chrononutrition() -> None:
    try:
        from nutev.analysis import relevance as relevance_module
    except Exception:
        return

    relevance_module.POSITIVE_TITLE_RULES.update(
        {
            "chrononutrition": 5,
            "chrono-nutrition": 5,
            "meal timing": 4,
            "time-restricted feeding": 5,
            "time restricted feeding": 5,
            "early time-restricted eating": 5,
            "early time restricted eating": 5,
        }
    )
    busca2b_bonus = relevance_module.WORKSTREAM_BONUS.setdefault("busca2b", {})
    busca2b_bonus.update(
        {
            "chrononutrition": 5,
            "chrono-nutrition": 5,
            "meal timing": 4,
            "time-restricted feeding": 5,
            "time restricted feeding": 5,
            "early time-restricted eating": 5,
            "early time restricted eating": 5,
        }
    )


_patch_final_querypack_terms()
_patch_query_builder_chrononutrition()
_patch_global_watch_chrononutrition()
_patch_relevance_chrononutrition()
