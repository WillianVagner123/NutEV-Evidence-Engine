from __future__ import annotations

from nutev.querypacks import semantic_blocks

DIETARY_FAT_QUALITY_TERMS = [
    "dietary fat quality",
    "dietary fat quality for cardiometabolic risk",
    "dietary fat quality for dyslipidemia",
    "dietary fat quality for type 2 diabetes",
    "fat quality index",
    "fat quality score",
    "saturated fat reduction",
    "saturated fatty acid reduction",
    "saturated fat replacement",
    "saturated fatty acid replacement",
    "replace saturated fat",
    "replacement of saturated fat",
    "unsaturated fat replacement",
    "unsaturated fatty acid replacement",
    "monounsaturated fat",
    "monounsaturated fatty acid",
    "polyunsaturated fat",
    "polyunsaturated fatty acid",
    "mufa",
    "pufa",
    "omega-3 fatty acid",
    "omega 3 fatty acid",
    "omega-3 intake",
    "omega 3 intake",
    "alpha-linolenic acid",
    "linoleic acid",
    "trans fat reduction",
    "trans fatty acid reduction",
    "industrial trans fat",
    "dietary cholesterol reduction",
    "low saturated fat diet",
    "heart-healthy fat",
    "heart healthy fat",
    "cardioprotective dietary fat",
    "dietary fat dyslipidemia",
    "dietary fat dyslipidaemia",
    "dietary fat ldl cholesterol",
    "dietary fat apolipoprotein b",
    "dietary fat apo b",
    "dietary fat triglycerides",
    "dietary fat hypertriglyceridemia",
    "dietary fat hypertriglyceridaemia",
]

DIETARY_FAT_QUALITY_DOCUMENT_TERMS = [
    "dietary fat quality guideline",
    "dietary fat quality systematic review",
    "dietary fat quality meta-analysis",
    "dietary fat quality intervention trial",
    "saturated fat reduction guideline",
    "saturated fat reduction systematic review",
    "saturated fat replacement systematic review",
    "saturated fatty acid replacement systematic review",
    "unsaturated fat replacement systematic review",
    "polyunsaturated fat systematic review",
    "monounsaturated fat systematic review",
    "omega-3 fatty acid systematic review",
    "omega 3 fatty acid systematic review",
    "trans fat reduction guideline",
    "dietary cholesterol guideline",
    "dietary fat dyslipidemia guideline",
    "dietary fat dyslipidaemia guideline",
    "dietary fat ldl cholesterol guideline",
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


def apply_dietary_fat_quality_extensions() -> None:
    _extend_semantic_block(
        "dietary_fat_quality",
        terms=DIETARY_FAT_QUALITY_TERMS,
        document_terms=DIETARY_FAT_QUALITY_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "dietary_fat_quality",
        {"busca1": 3, "busca2a": 5, "busca2b": 5},
    )
