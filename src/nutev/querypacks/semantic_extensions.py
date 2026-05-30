from __future__ import annotations

from nutev.querypacks import semantic_blocks

CARDIOVASCULAR_KIDNEY_METABOLIC_TERMS = [
    "cardiovascular-kidney-metabolic syndrome",
    "cardiovascular kidney metabolic syndrome",
    "cardiovascular-kidney-metabolic health",
    "cardiovascular kidney metabolic health",
    "cardiovascular-kidney-metabolic risk",
    "cardiovascular kidney metabolic risk",
    "ckm syndrome",
    "ckm health",
    "ckm risk",
]

CARDIOVASCULAR_KIDNEY_METABOLIC_DOCUMENT_TERMS = [
    "scientific statement",
    "presidential advisory",
    "clinical practice guideline",
    "consensus statement",
    "clinical decision pathway",
    "practice guidance",
    "systematic review",
]

DIGITAL_NUTRITION_ADHERENCE_TERMS = [
    "digital nutrition intervention",
    "digital dietary intervention",
    "app-based nutrition intervention",
    "app based nutrition intervention",
    "mobile nutrition intervention",
    "mobile dietary intervention",
    "nutrition app",
    "dietary app",
    "mobile dietary self-monitoring",
    "digital dietary self-monitoring",
    "remote dietitian coaching",
    "telehealth nutrition counseling",
    "telehealth nutrition counselling",
    "virtual nutrition counseling",
    "virtual nutrition counselling",
]

DIGITAL_NUTRITION_ADHERENCE_DOCUMENT_TERMS = [
    "digital health intervention",
    "behavior change intervention",
    "behaviour change intervention",
    "implementation study",
    "implementation trial",
    "process evaluation",
    "pragmatic trial",
    "randomized controlled trial",
    "hybrid effectiveness-implementation",
]

FOOD_AS_MEDICINE_SERVICE_TERMS = [
    "food pharmacy",
    "food pharmacy program",
    "food pantry intervention",
    "food pantry program",
    "medically tailored food intervention",
    "medically tailored food program",
    "produce prescription intervention",
    "produce prescription trial",
    "fruit and vegetable prescription program",
    "fruit and vegetable prescription intervention",
]

FOOD_AS_MEDICINE_SERVICE_DOCUMENT_TERMS = [
    "food pharmacy program",
    "food pantry intervention",
    "produce prescription intervention",
    "produce prescription trial",
    "fruit and vegetable prescription program",
    "implementation study",
    "implementation trial",
    "quality improvement study",
    "policy evaluation",
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


def _extend_block(block_name: str, terms: list[str], document_terms: list[str]) -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
        block_name,
        {"terms": [], "document_terms": []},
    )
    block["terms"] = _extend_unique(block.setdefault("terms", []), terms)
    block["document_terms"] = _extend_unique(
        block.setdefault("document_terms", []),
        document_terms,
    )


def apply_semantic_extensions() -> None:
    _extend_block(
        "cardiometabolic_precision",
        CARDIOVASCULAR_KIDNEY_METABOLIC_TERMS,
        CARDIOVASCULAR_KIDNEY_METABOLIC_DOCUMENT_TERMS,
    )
    _extend_block(
        "adherence_persistence",
        DIGITAL_NUTRITION_ADHERENCE_TERMS,
        DIGITAL_NUTRITION_ADHERENCE_DOCUMENT_TERMS,
    )
    _extend_block(
        "implementation_science",
        DIGITAL_NUTRITION_ADHERENCE_TERMS,
        DIGITAL_NUTRITION_ADHERENCE_DOCUMENT_TERMS,
    )
    _extend_block(
        "food_prescription_programs",
        FOOD_AS_MEDICINE_SERVICE_TERMS,
        FOOD_AS_MEDICINE_SERVICE_DOCUMENT_TERMS,
    )


apply_semantic_extensions()
