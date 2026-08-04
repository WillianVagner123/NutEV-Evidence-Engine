from __future__ import annotations

from nutev.querypacks import semantic_blocks

CKM_KIDNEY_NUTRITION_TERMS = [
    "cardiovascular-kidney-metabolic nutrition",
    "cardiovascular kidney metabolic nutrition",
    "cardiovascular-kidney-metabolic nutrition care",
    "cardiovascular kidney metabolic nutrition care",
    "ckm nutrition",
    "ckm syndrome nutrition",
    "ckm syndrome nutrition care",
    "cardiometabolic renal nutrition",
    "chronic kidney disease nutrition",
    "chronic kidney disease nutrition therapy",
    "ckd nutrition",
    "ckd nutrition therapy",
    "kidney disease nutrition",
    "kidney disease nutrition therapy",
    "renal nutrition therapy",
    "renal diet",
    "kidney-friendly diet",
    "kidney friendly diet",
    "diabetic kidney disease nutrition",
    "diabetic kidney disease nutrition therapy",
    "hypertension chronic kidney disease diet",
    "dash diet chronic kidney disease",
    "dash chronic kidney disease",
    "dietary sodium restriction chronic kidney disease",
    "dietary sodium restriction ckd",
    "sodium reduction chronic kidney disease",
    "sodium reduction ckd",
    "protein intake chronic kidney disease",
    "protein restriction chronic kidney disease",
    "low protein diet chronic kidney disease",
    "plant-dominant low-protein diet",
    "plant dominant low protein diet",
    "plado diet",
    "potassium management chronic kidney disease",
    "potassium management ckd",
    "phosphate management chronic kidney disease",
    "phosphate management ckd",
]

CKM_KIDNEY_NUTRITION_DOCUMENT_TERMS = [
    "cardiovascular-kidney-metabolic scientific statement",
    "cardiovascular kidney metabolic scientific statement",
    "ckm scientific statement",
    "ckm syndrome scientific statement",
    "chronic kidney disease nutrition guideline",
    "chronic kidney disease nutrition practice guideline",
    "ckd nutrition guideline",
    "ckd nutrition practice guideline",
    "kidney disease nutrition guideline",
    "renal nutrition guideline",
    "renal nutrition consensus",
    "diabetic kidney disease nutrition guideline",
    "diabetic kidney disease nutrition consensus",
    "kdigo chronic kidney disease guideline nutrition",
    "kdigo ckd guideline nutrition",
    "kdoqi nutrition guideline",
    "kdoqi nutrition practice guideline",
    "low protein diet chronic kidney disease systematic review",
    "protein restriction chronic kidney disease systematic review",
    "plant-dominant low-protein diet review",
    "plant dominant low protein diet review",
    "dietary sodium restriction ckd systematic review",
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


def _prioritize_semantic_block(block_name: str, priorities: dict[str, int]) -> None:
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


def apply_ckm_kidney_nutrition_extensions() -> None:
    _extend_semantic_block(
        "cardiometabolic_kidney_nutrition",
        terms=CKM_KIDNEY_NUTRITION_TERMS,
        document_terms=CKM_KIDNEY_NUTRITION_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "cardiometabolic_kidney_nutrition",
        {"busca2a": 5, "busca2b": 5},
    )
    for block_name in (
        "cardiometabolic_precision",
        "nutrition_care_delivery",
        "lifestyle_nutrition_patterns",
    ):
        _extend_semantic_block(
            block_name,
            terms=CKM_KIDNEY_NUTRITION_TERMS,
            document_terms=CKM_KIDNEY_NUTRITION_DOCUMENT_TERMS,
        )


apply_ckm_kidney_nutrition_extensions()
