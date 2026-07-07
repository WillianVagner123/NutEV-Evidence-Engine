from __future__ import annotations

from nutev.querypacks import semantic_blocks

CARDIOMETABOLIC_PREVENTION_TERMS = [
    "diabetes prevention program",
    "diabetes prevention programme",
    "diabetes prevention programs",
    "diabetes prevention programmes",
    "national diabetes prevention program",
    "national diabetes prevention programme",
    "cdc diabetes prevention program",
    "cdc diabetes prevention programme",
    "diabetes prevention recognition program",
    "diabetes prevention recognition programme",
    "diabetes prevention lifestyle intervention",
    "diabetes prevention lifestyle program",
    "diabetes prevention lifestyle programme",
    "dpp lifestyle intervention",
    "dpp lifestyle program",
    "dpp lifestyle programme",
    "translational diabetes prevention",
    "diabetes prevention translation",
    "community diabetes prevention",
    "primary care diabetes prevention",
    "prediabetes lifestyle intervention",
    "prediabetes lifestyle program",
    "prediabetes lifestyle programme",
    "prediabetes dietary intervention",
    "prediabetes nutrition intervention",
    "prediabetes weight loss intervention",
    "cardiometabolic prevention",
    "cardiometabolic risk reduction program",
    "cardiometabolic risk reduction programme",
    "cardiometabolic lifestyle intervention",
    "cardiometabolic lifestyle program",
    "cardiometabolic lifestyle programme",
]

CARDIOMETABOLIC_REMISSION_TERMS = [
    "diabetes remission maintenance",
    "type 2 diabetes remission maintenance",
    "remission maintenance",
    "weight loss maintenance program",
    "weight loss maintenance programme",
    "weight loss maintenance intervention",
    "weight regain prevention program",
    "weight regain prevention programme",
    "weight regain prevention intervention",
    "relapse prevention for weight loss",
    "relapse prevention weight loss",
    "dietary relapse prevention",
    "long-term diabetes remission",
    "long term diabetes remission",
    "sustained diabetes remission",
    "sustained weight loss maintenance",
]

CARDIOMETABOLIC_PREVENTION_DOCUMENT_TERMS = [
    "diabetes prevention program trial",
    "diabetes prevention programme trial",
    "diabetes prevention program implementation",
    "diabetes prevention programme implementation",
    "diabetes prevention program evaluation",
    "diabetes prevention programme evaluation",
    "diabetes prevention program systematic review",
    "diabetes prevention programme systematic review",
    "diabetes prevention program meta-analysis",
    "diabetes prevention programme meta-analysis",
    "national diabetes prevention program evaluation",
    "national diabetes prevention programme evaluation",
    "cdc diabetes prevention program evaluation",
    "cdc diabetes prevention programme evaluation",
    "prediabetes lifestyle intervention trial",
    "prediabetes lifestyle intervention systematic review",
    "prediabetes dietary intervention trial",
    "prediabetes nutrition intervention trial",
    "translational diabetes prevention study",
    "community diabetes prevention implementation",
    "primary care diabetes prevention implementation",
]

CARDIOMETABOLIC_REMISSION_DOCUMENT_TERMS = [
    "diabetes remission maintenance trial",
    "type 2 diabetes remission maintenance trial",
    "diabetes remission maintenance systematic review",
    "type 2 diabetes remission maintenance systematic review",
    "weight loss maintenance program evaluation",
    "weight loss maintenance programme evaluation",
    "weight loss maintenance intervention trial",
    "weight regain prevention intervention trial",
    "weight regain prevention systematic review",
    "relapse prevention weight loss trial",
    "dietary relapse prevention trial",
    "sustained diabetes remission study",
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


def apply_cardiometabolic_prevention_extensions() -> None:
    prevention_terms = CARDIOMETABOLIC_PREVENTION_TERMS + CARDIOMETABOLIC_REMISSION_TERMS
    prevention_document_terms = (
        CARDIOMETABOLIC_PREVENTION_DOCUMENT_TERMS
        + CARDIOMETABOLIC_REMISSION_DOCUMENT_TERMS
    )
    for block_name in (
        "cardiometabolic_precision",
        "adherence_persistence",
        "lifestyle_nutrition_patterns",
        "implementation_science",
    ):
        _extend_semantic_block(
            block_name,
            terms=prevention_terms,
            document_terms=prevention_document_terms,
        )
    _prioritize_semantic_block(
        "cardiometabolic_precision",
        {"busca2a": 5, "busca2b": 5},
    )
    _prioritize_semantic_block(
        "adherence_persistence",
        {"busca2b": 5},
    )
