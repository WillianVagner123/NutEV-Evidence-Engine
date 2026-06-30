from __future__ import annotations

from nutev.querypacks import semantic_blocks

ADHERENCE_IMPLEMENTATION_TERMS = [
    "dietary habit formation",
    "dietary habits",
    "healthy eating habit formation",
    "habit-based dietary intervention",
    "habit based dietary intervention",
    "dietary action planning",
    "dietary coping planning",
    "dietary goal setting",
    "dietary problem solving",
    "dietary relapse prevention",
    "dietary lapse management",
    "implementation intentions for diet",
    "self-regulation of dietary behavior",
    "self regulation of dietary behavior",
    "dietary self-management support",
    "dietary self management support",
    "nutrition self-management support",
    "nutrition self management support",
    "maintenance of dietary behavior change",
    "maintenance of dietary behaviour change",
    "long-term dietary behavior change",
    "long term dietary behavior change",
    "long-term dietary behaviour change",
    "long term dietary behaviour change",
    "adherence to dietary patterns",
    "adherence to mediterranean diet",
    "adherence to dash diet",
    "adherence to plant-based diet",
    "adherence to plant based diet",
]

ADHERENCE_IMPLEMENTATION_DOCUMENT_TERMS = [
    "dietary adherence intervention",
    "dietary habit formation intervention",
    "habit-based dietary intervention",
    "habit based dietary intervention",
    "dietary action planning intervention",
    "dietary coping planning intervention",
    "dietary goal setting intervention",
    "dietary relapse prevention intervention",
    "dietary self-management support intervention",
    "nutrition self-management support intervention",
    "dietary behavior maintenance trial",
    "dietary behaviour maintenance trial",
    "long-term dietary behavior change trial",
    "long term dietary behavior change trial",
    "long-term dietary behaviour change trial",
    "long term dietary behaviour change trial",
    "dietary adherence systematic review",
    "dietary adherence meta-analysis",
]

NUTRITION_IMPLEMENTATION_STUDY_TERMS = [
    "nutrition implementation science",
    "nutrition implementation research",
    "nutrition implementation strategy",
    "nutrition implementation strategies",
    "nutrition implementation outcomes",
    "nutrition implementation fidelity",
    "nutrition implementation determinants",
    "nutrition implementation barriers",
    "nutrition implementation facilitators",
    "dietary intervention implementation",
    "dietary intervention fidelity",
    "dietary intervention reach",
    "dietary intervention adoption",
    "dietary intervention sustainment",
    "nutrition program implementation",
    "nutrition program evaluation",
    "lifestyle program implementation",
    "lifestyle program evaluation",
    "pragmatic nutrition trial",
    "pragmatic dietary trial",
    "pragmatic lifestyle trial",
    "hybrid effectiveness-implementation nutrition",
    "hybrid effectiveness implementation nutrition",
    "hybrid effectiveness-implementation dietary",
    "hybrid effectiveness implementation dietary",
    "type 1 hybrid nutrition trial",
    "type 2 hybrid nutrition trial",
    "type 3 hybrid nutrition trial",
]

NUTRITION_IMPLEMENTATION_DOCUMENT_TERMS = [
    "nutrition implementation study",
    "nutrition implementation trial",
    "nutrition implementation evaluation",
    "nutrition program implementation study",
    "nutrition program evaluation",
    "dietary intervention implementation study",
    "dietary intervention fidelity study",
    "dietary intervention process evaluation",
    "pragmatic nutrition trial",
    "pragmatic dietary trial",
    "pragmatic lifestyle trial",
    "hybrid effectiveness-implementation nutrition trial",
    "hybrid effectiveness implementation nutrition trial",
    "hybrid effectiveness-implementation dietary trial",
    "hybrid effectiveness implementation dietary trial",
]


def _extend_unique(existing: list[str], additions: list[str]) -> list[str]:
    seen = {item.lower() for item in existing}
    for item in additions:
        value = item.strip()
        if not value or value.lower() in seen:
            continue
        existing.append(value)
        seen.add(value.lower())
    return existing


def _extend_semantic_block(
    block_name: str,
    *,
    terms: list[str],
    document_terms: list[str],
) -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
        block_name,
        {"terms": [], "document_terms": []},
    )
    block["terms"] = _extend_unique(block.setdefault("terms", []), terms)
    block["document_terms"] = _extend_unique(
        block.setdefault("document_terms", []),
        document_terms,
    )


def apply_adherence_implementation_extensions() -> None:
    for block_name in ("adherence_persistence", "lifestyle_nutrition_patterns"):
        _extend_semantic_block(
            block_name,
            terms=ADHERENCE_IMPLEMENTATION_TERMS,
            document_terms=ADHERENCE_IMPLEMENTATION_DOCUMENT_TERMS,
        )
    for block_name in ("implementation_science", "nutrition_care_delivery"):
        _extend_semantic_block(
            block_name,
            terms=NUTRITION_IMPLEMENTATION_STUDY_TERMS,
            document_terms=NUTRITION_IMPLEMENTATION_DOCUMENT_TERMS,
        )
