from __future__ import annotations

from nutev.querypacks import semantic_blocks

MASLD_DIET_TERMS = [
    "MASLD diet",
    "MASLD dietary intervention",
    "MASLD nutrition therapy",
    "MASLD lifestyle intervention",
    "MASLD weight loss",
    "MASLD weight management",
    "MASLD Mediterranean diet",
    "MASLD low calorie diet",
    "MASLD low-calorie diet",
    "MASLD hypocaloric diet",
    "MASLD dietary pattern",
    "MASLD cardiometabolic risk",
    "MASH diet",
    "MASH dietary intervention",
    "MASH nutrition therapy",
    "MASH lifestyle intervention",
    "MASH weight loss",
    "MASH Mediterranean diet",
    "NAFLD diet",
    "NAFLD dietary intervention",
    "NAFLD nutrition therapy",
    "NAFLD lifestyle intervention",
    "NAFLD weight loss",
    "NAFLD weight management",
    "NAFLD Mediterranean diet",
    "NAFLD low calorie diet",
    "NAFLD low-calorie diet",
    "NAFLD hypocaloric diet",
    "NAFLD dietary pattern",
    "NAFLD cardiometabolic risk",
    "NASH diet",
    "NASH dietary intervention",
    "NASH nutrition therapy",
    "NASH lifestyle intervention",
    "NASH weight loss",
    "NASH Mediterranean diet",
    "steatotic liver disease diet",
    "steatotic liver disease dietary intervention",
    "steatotic liver disease nutrition therapy",
    "steatotic liver disease lifestyle intervention",
    "steatotic liver disease weight loss",
    "fatty liver diet",
    "fatty liver dietary intervention",
    "fatty liver nutrition therapy",
    "fatty liver lifestyle intervention",
    "fatty liver weight loss",
]

MASLD_DIET_DOCUMENT_TERMS = [
    "MASLD clinical practice guideline",
    "MASLD practice guidance",
    "MASLD consensus statement",
    "MASLD consensus report",
    "MASLD systematic review",
    "MASLD meta-analysis",
    "MASLD umbrella review",
    "MASLD dietary intervention trial",
    "MASLD lifestyle intervention trial",
    "MASLD nutrition therapy guideline",
    "MASH clinical practice guideline",
    "MASH practice guidance",
    "MASH systematic review",
    "MASH dietary intervention trial",
    "NAFLD clinical practice guideline",
    "NAFLD practice guidance",
    "NAFLD consensus statement",
    "NAFLD consensus report",
    "NAFLD systematic review",
    "NAFLD meta-analysis",
    "NAFLD umbrella review",
    "NAFLD dietary intervention trial",
    "NAFLD lifestyle intervention trial",
    "NAFLD nutrition therapy guideline",
    "NASH clinical practice guideline",
    "NASH practice guidance",
    "NASH systematic review",
    "NASH dietary intervention trial",
    "steatotic liver disease clinical practice guideline",
    "steatotic liver disease practice guidance",
    "steatotic liver disease systematic review",
    "steatotic liver disease dietary intervention trial",
    "fatty liver dietary intervention trial",
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


def apply_masld_diet_extensions() -> None:
    _extend_semantic_block(
        "masld_diet_lifestyle",
        terms=MASLD_DIET_TERMS,
        document_terms=MASLD_DIET_DOCUMENT_TERMS,
    )
    for block_name in ("cardiometabolic_liver", "evidence_synthesis"):
        _extend_semantic_block(
            block_name,
            terms=MASLD_DIET_TERMS,
            document_terms=MASLD_DIET_DOCUMENT_TERMS,
        )
    _prioritize_semantic_block(
        "masld_diet_lifestyle",
        {"busca2a": 5, "busca2b": 5, "busca1": 3},
    )
