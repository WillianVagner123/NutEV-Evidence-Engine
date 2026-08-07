from __future__ import annotations

from nutev.querypacks import semantic_blocks

PORTFOLIO_LIPID_PATTERN_TERMS = [
    "portfolio diet",
    "portfolio dietary pattern",
    "portfolio diet score",
    "portfolio dietary score",
    "portfolio diet adherence",
    "portfolio dietary pattern adherence",
    "cholesterol-lowering diet",
    "cholesterol lowering diet",
    "ldl cholesterol lowering diet",
    "ldl-c lowering diet",
    "lipid-lowering dietary pattern",
    "lipid lowering dietary pattern",
    "dietary portfolio for cholesterol lowering",
    "dietary portfolio for dyslipidemia",
    "dietary portfolio for dyslipidaemia",
    "dietary portfolio for cardiometabolic risk",
    "portfolio diet for cardiometabolic risk",
    "portfolio diet for hypercholesterolemia",
    "portfolio diet for hypercholesterolaemia",
    "portfolio diet for dyslipidemia",
    "portfolio diet for dyslipidaemia",
    "plant sterols",
    "plant stanols",
    "viscous fiber",
    "viscous fibre",
    "soluble fiber cholesterol",
    "soluble fibre cholesterol",
    "nuts cholesterol lowering",
    "soy protein cholesterol",
]

PORTFOLIO_LIPID_PATTERN_DOCUMENT_TERMS = [
    "portfolio diet systematic review",
    "portfolio diet meta-analysis",
    "portfolio diet randomized trial",
    "portfolio diet randomised trial",
    "portfolio diet intervention trial",
    "portfolio diet guideline",
    "portfolio diet consensus",
    "portfolio diet cardiometabolic systematic review",
    "portfolio dietary pattern systematic review",
    "portfolio dietary pattern meta-analysis",
    "cholesterol-lowering diet systematic review",
    "cholesterol lowering diet systematic review",
    "ldl cholesterol lowering diet trial",
    "lipid-lowering dietary pattern trial",
    "lipid lowering dietary pattern trial",
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
    block_name: str, priorities: dict[str, int]) -> None:
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


def apply_portfolio_lipid_extensions() -> None:
    _extend_semantic_block(
        "portfolio_lipid_pattern",
        terms=PORTFOLIO_LIPID_PATTERN_TERMS,
        document_terms=PORTFOLIO_LIPID_PATTERN_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "portfolio_lipid_pattern",
        {"busca2a": 5, "busca2b": 5, "busca1": 3},
    )
