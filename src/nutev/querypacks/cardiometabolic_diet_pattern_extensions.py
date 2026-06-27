from __future__ import annotations

from nutev.querypacks import semantic_blocks

CARDIOMETABOLIC_DIET_PATTERN_TERMS = [
    "cardioprotective diet",
    "cardioprotective dietary pattern",
    "cardiometabolic dietary pattern",
    "cardiometabolic diet quality",
    "heart-healthy diet",
    "heart healthy diet",
    "heart-healthy dietary pattern",
    "heart healthy dietary pattern",
    "cholesterol-lowering diet",
    "cholesterol lowering diet",
    "cholesterol-lowering dietary pattern",
    "cholesterol lowering dietary pattern",
    "lipid-lowering diet",
    "lipid lowering diet",
    "lipid-lowering dietary pattern",
    "lipid lowering dietary pattern",
    "portfolio dietary pattern",
    "dietary portfolio",
    "portfolio diet for cholesterol",
    "portfolio diet for dyslipidemia",
    "portfolio diet for dyslipidaemia",
    "portfolio diet cardiometabolic risk",
    "mind dietary pattern",
    "mind diet cardiometabolic risk",
    "dash dietary pattern",
    "dash diet for hypertension",
    "dash diet blood pressure",
    "low-sodium diet",
    "low sodium diet",
    "sodium reduction diet",
    "dietary sodium reduction",
    "anti-inflammatory diet",
    "anti inflammatory diet",
    "anti-inflammatory dietary pattern",
    "anti inflammatory dietary pattern",
]

CARDIOMETABOLIC_DIET_PATTERN_DOCUMENT_TERMS = [
    "cardioprotective diet guideline",
    "cardioprotective diet systematic review",
    "cardioprotective dietary pattern systematic review",
    "cardiometabolic dietary pattern systematic review",
    "heart-healthy diet guideline",
    "heart healthy diet guideline",
    "cholesterol-lowering diet guideline",
    "cholesterol lowering diet guideline",
    "cholesterol-lowering diet systematic review",
    "cholesterol lowering diet systematic review",
    "lipid-lowering diet systematic review",
    "lipid lowering diet systematic review",
    "portfolio diet guideline",
    "portfolio diet systematic review",
    "portfolio diet meta-analysis",
    "portfolio diet intervention trial",
    "portfolio diet dyslipidemia trial",
    "portfolio diet dyslipidaemia trial",
    "mind diet systematic review",
    "mind diet meta-analysis",
    "mind diet intervention trial",
    "dash diet guideline",
    "dash diet systematic review",
    "dash diet meta-analysis",
    "dash diet intervention trial",
    "low-sodium diet guideline",
    "low sodium diet guideline",
    "sodium reduction guideline",
    "dietary sodium reduction systematic review",
    "anti-inflammatory diet systematic review",
    "anti inflammatory diet systematic review",
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


def _prioritize_semantic_block(
    block_name: str,
    priorities: dict[str, int],
) -> None:
    for workstream, priority in priorities.items():
        existing = [
            (name, value)
            for name, value in semantic_blocks.WORKSTREAM_SEMANTIC_PRIORITIES.get(
                workstream,
                [],
            )
            if name != block_name
        ]
        semantic_blocks.WORKSTREAM_SEMANTIC_PRIORITIES[workstream] = [
            (block_name, priority),
            *existing,
        ]


def apply_cardiometabolic_diet_pattern_extensions() -> None:
    _extend_semantic_block(
        "cardiometabolic_diet_patterns",
        terms=CARDIOMETABOLIC_DIET_PATTERN_TERMS,
        document_terms=CARDIOMETABOLIC_DIET_PATTERN_DOCUMENT_TERMS,
    )
    _extend_semantic_block(
        "lifestyle_nutrition_patterns",
        terms=CARDIOMETABOLIC_DIET_PATTERN_TERMS,
        document_terms=CARDIOMETABOLIC_DIET_PATTERN_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "cardiometabolic_diet_patterns",
        {"busca1": 3, "busca2a": 4, "busca2b": 5},
    )
