from __future__ import annotations

from nutev.querypacks import semantic_blocks

GROUP_CARE_IMPLEMENTATION_TERMS = [
    "group visit",
    "group visits",
    "group medical visit",
    "group medical visits",
    "shared medical appointment",
    "shared medical appointments",
    "group-based lifestyle intervention",
    "group based lifestyle intervention",
    "group-based nutrition intervention",
    "group based nutrition intervention",
    "group-based weight management",
    "group based weight management",
    "group lifestyle program",
    "group lifestyle programme",
    "group nutrition education",
    "diabetes self-management education",
    "diabetes self management education",
    "diabetes self-management support",
    "diabetes self management support",
    "diabetes self-management education and support",
    "diabetes self management education and support",
    "DSMES",
    "DSME",
]

GROUP_CARE_DOCUMENT_TERMS = [
    "group visit trial",
    "group medical visit trial",
    "shared medical appointment trial",
    "group-based lifestyle intervention trial",
    "group based lifestyle intervention trial",
    "group-based nutrition intervention trial",
    "group based nutrition intervention trial",
    "group-based weight management trial",
    "group based weight management trial",
    "diabetes self-management education trial",
    "diabetes self management education trial",
    "diabetes self-management support trial",
    "diabetes self management support trial",
    "diabetes self-management education and support guideline",
    "diabetes self management education and support guideline",
    "DSMES guideline",
    "DSMES consensus report",
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


def apply_group_care_extensions() -> None:
    for block_name in (
        "implementation_science",
        "adherence_persistence",
        "nutrition_care_delivery",
    ):
        _extend_semantic_block(
            block_name,
            terms=GROUP_CARE_IMPLEMENTATION_TERMS,
            document_terms=GROUP_CARE_DOCUMENT_TERMS,
        )
