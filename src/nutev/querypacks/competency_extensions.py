from __future__ import annotations

from nutev.querypacks import semantic_blocks

PROFESSIONAL_COMPETENCY_FRAMEWORK_TERMS = [
    "lifestyle medicine competencies",
    "lifestyle medicine competency",
    "lifestyle medicine competency framework",
    "lifestyle medicine competency frameworks",
    "nutrition competencies",
    "nutrition competency",
    "nutrition competency framework",
    "nutrition competency frameworks",
    "nutrition care competencies",
    "nutrition counseling competencies",
    "nutrition counselling competencies",
    "culinary medicine competencies",
    "culinary medicine competency",
    "culinary medicine competency framework",
    "culinary nutrition competencies",
    "culinary nutrition competency",
    "food literacy competencies",
    "food literacy competency",
    "food skills competencies",
    "food skills competency",
    "cooking skills competencies",
    "cooking skills competency",
    "commensality competencies",
    "commensality competency",
    "dietary counseling competencies",
    "dietary counselling competencies",
    "lifestyle counseling competencies",
    "lifestyle counselling competencies",
    "behavior change counseling competencies",
    "behaviour change counselling competencies",
    "health coaching competencies",
    "health coaching competency",
]

PROFESSIONAL_COMPETENCY_FRAMEWORK_DOCUMENT_TERMS = [
    "competency framework",
    "competency frameworks",
    "competency statement",
    "competency statements",
    "core competencies",
    "professional competencies",
    "lifestyle medicine competency framework",
    "lifestyle medicine competencies",
    "nutrition competency framework",
    "nutrition competencies",
    "culinary medicine competency framework",
    "culinary medicine competencies",
    "food literacy competency framework",
    "food skills competency framework",
    "curriculum competencies",
    "training competencies",
    "practice competencies",
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


def apply_competency_extensions() -> None:
    block_name = "professional_competency_frameworks"
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
        block_name,
        {"terms": [], "document_terms": []},
    )
    block["terms"] = _extend_unique(
        block.setdefault("terms", []),
        PROFESSIONAL_COMPETENCY_FRAMEWORK_TERMS,
    )
    block["document_terms"] = _extend_unique(
        block.setdefault("document_terms", []),
        PROFESSIONAL_COMPETENCY_FRAMEWORK_DOCUMENT_TERMS,
    )

    priorities = [
        (block_name, 5),
        *[
            (name, priority)
            for name, priority in semantic_blocks.WORKSTREAM_SEMANTIC_PRIORITIES.get(
                "artigo3_framework",
                [],
            )
            if name != block_name
        ],
    ]
    semantic_blocks.WORKSTREAM_SEMANTIC_PRIORITIES["artigo3_framework"] = priorities
