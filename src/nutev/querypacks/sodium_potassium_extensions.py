from __future__ import annotations

from nutev.querypacks import semantic_blocks

SODIUM_POTASSIUM_BLOOD_PRESSURE_TERMS = [
    "dietary sodium",
    "sodium intake",
    "sodium reduction",
    "salt reduction",
    "low sodium diet",
    "low-sodium diet",
    "reduced sodium diet",
    "dietary salt",
    "salt intake",
    "salt restriction",
    "sodium restriction",
    "sodium-to-potassium ratio",
    "sodium potassium ratio",
    "dietary potassium",
    "potassium intake",
    "potassium supplementation",
    "potassium-rich diet",
    "potassium rich diet",
    "potassium-enriched salt",
    "potassium enriched salt",
    "potassium salt substitute",
    "salt substitute",
    "salt substitutes",
    "reduced sodium salt substitute",
    "dash sodium",
    "dash-sodium",
    "dietary approaches to stop hypertension sodium",
    "blood pressure diet",
    "dietary blood pressure intervention",
    "hypertension dietary intervention",
    "hypertension nutrition therapy",
    "cardiometabolic blood pressure diet",
]

SODIUM_POTASSIUM_BLOOD_PRESSURE_DOCUMENT_TERMS = [
    "sodium reduction guideline",
    "salt reduction guideline",
    "dietary sodium guideline",
    "dietary sodium systematic review",
    "dietary sodium meta-analysis",
    "sodium reduction intervention trial",
    "salt reduction intervention trial",
    "potassium supplementation guideline",
    "potassium supplementation systematic review",
    "potassium supplementation meta-analysis",
    "salt substitute trial",
    "salt substitute systematic review",
    "potassium-enriched salt trial",
    "potassium enriched salt trial",
    "dash sodium trial",
    "dash-sodium trial",
    "blood pressure dietary guideline",
    "hypertension dietary guideline",
    "hypertension nutrition guideline",
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


def apply_sodium_potassium_extensions() -> None:
    _extend_semantic_block(
        "dietary_sodium_potassium_bp",
        terms=SODIUM_POTASSIUM_BLOOD_PRESSURE_TERMS,
        document_terms=SODIUM_POTASSIUM_BLOOD_PRESSURE_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "dietary_sodium_potassium_bp",
        {"busca1": 4, "busca2a": 5, "busca2b": 5},
    )
