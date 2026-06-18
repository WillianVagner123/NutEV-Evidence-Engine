from __future__ import annotations

from nutev.querypacks import semantic_blocks

HEPATIC_STEATOSIS_NUTRITION_TERMS = [
    "hepatic steatosis",
    "liver steatosis",
    "liver fat",
    "intrahepatic fat",
    "intrahepatic triglyceride",
    "intrahepatic triglycerides",
    "hepatic fat content",
    "liver fat content",
    "hepatic fat accumulation",
    "hepatic lipid accumulation",
    "ectopic liver fat",
    "liver fat reduction",
]

HEPATIC_STEATOSIS_NUTRITION_DOCUMENT_TERMS = [
    "hepatic steatosis guideline",
    "hepatic steatosis practice guidance",
    "hepatic steatosis consensus",
    "hepatic steatosis systematic review",
    "hepatic steatosis meta-analysis",
    "dietary intervention for hepatic steatosis",
    "nutrition intervention for hepatic steatosis",
    "lifestyle intervention for hepatic steatosis",
    "liver fat reduction trial",
    "liver fat reduction systematic review",
]

HEPATIC_STEATOSIS_TARGET_BLOCKS = (
    "cardiometabolic_liver",
    "cardiometabolic_precision",
    "lifestyle_nutrition_patterns",
)


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


def apply_hepatic_steatosis_extensions() -> None:
    for block_name in HEPATIC_STEATOSIS_TARGET_BLOCKS:
        _extend_semantic_block(
            block_name,
            terms=HEPATIC_STEATOSIS_NUTRITION_TERMS,
            document_terms=HEPATIC_STEATOSIS_NUTRITION_DOCUMENT_TERMS,
        )
