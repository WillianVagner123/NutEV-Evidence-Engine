from __future__ import annotations

from nutev.querypacks import semantic_blocks

OBESITY_CARE_PATHWAY_TERMS = [
    "obesity care pathway",
    "obesity care pathways",
    "obesity care model",
    "obesity care models",
    "obesity care protocol",
    "obesity care protocols",
    "obesity treatment pathway",
    "obesity treatment pathways",
    "obesity management pathway",
    "obesity management pathways",
    "comprehensive obesity care",
    "integrated obesity care",
    "multicomponent obesity intervention",
    "multicomponent obesity interventions",
    "multidisciplinary obesity care",
    "interdisciplinary obesity care",
    "team-based obesity care",
    "team based obesity care",
    "primary care obesity management",
    "primary care weight management",
    "clinical obesity pathway",
    "clinical obesity care",
    "chronic obesity care",
    "adiposity-based chronic disease care",
    "adiposity based chronic disease care",
]

OBESITY_CARE_PATHWAY_DOCUMENT_TERMS = [
    "obesity care pathway guideline",
    "obesity care pathway consensus",
    "obesity care protocol guideline",
    "obesity management pathway guideline",
    "comprehensive obesity care guideline",
    "integrated obesity care guideline",
    "primary care obesity management guideline",
    "primary care weight management guideline",
    "obesity care model implementation",
    "obesity care pathway implementation",
    "obesity treatment pathway implementation",
    "multidisciplinary obesity care implementation",
    "team-based obesity care implementation",
    "team based obesity care implementation",
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


def apply_obesity_care_pathway_extensions() -> None:
    for block_name in (
        "cardiometabolic_precision",
        "nutrition_care_delivery",
        "implementation_science",
        "lifestyle_nutrition_patterns",
    ):
        _extend_semantic_block(
            block_name,
            terms=OBESITY_CARE_PATHWAY_TERMS,
            document_terms=OBESITY_CARE_PATHWAY_DOCUMENT_TERMS,
        )
