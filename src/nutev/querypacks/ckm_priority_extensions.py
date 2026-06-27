from __future__ import annotations

from nutev.querypacks import semantic_blocks

CKM_QUERY_TERMS = [
    "cardiovascular-kidney-metabolic syndrome",
    "cardiovascular kidney metabolic syndrome",
    "cardiovascular-kidney-metabolic health",
    "cardiovascular kidney metabolic health",
    "cardiovascular-kidney-metabolic risk",
    "cardiovascular kidney metabolic risk",
    "ckm syndrome",
    "ckm health",
    "ckm risk",
    "cardiorenal metabolic syndrome",
    "cardio-renal-metabolic syndrome",
    "cardiorenal-metabolic syndrome",
    "cardiorenal metabolic health",
    "cardiorenal metabolic risk",
]

CKM_DOCUMENT_TERMS = [
    "scientific statement",
    "presidential advisory",
    "clinical practice guideline",
    "consensus statement",
    "clinical decision pathway",
    "practice guidance",
    "systematic review",
]


def _promote_terms(existing: list[str], preferred: list[str]) -> list[str]:
    by_lower = {term.lower(): term for term in existing}
    promoted = [term for term in preferred if term.lower() in by_lower]
    missing = [term for term in preferred if term.lower() not in by_lower]
    remaining = [term for term in existing if term.lower() not in {p.lower() for p in preferred}]
    return missing + promoted + remaining


def _promote_block_for_workstream(workstream: str, block_name: str, priority: int) -> None:
    current = semantic_blocks.WORKSTREAM_SEMANTIC_PRIORITIES.get(workstream, [])
    rest = [(name, value) for name, value in current if name != block_name]
    semantic_blocks.WORKSTREAM_SEMANTIC_PRIORITIES[workstream] = [(block_name, priority), *rest]


def apply_ckm_query_priority_extensions() -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
        "cardiometabolic_precision",
        {"terms": [], "document_terms": []},
    )
    block["terms"] = _promote_terms(block.setdefault("terms", []), CKM_QUERY_TERMS)
    block["document_terms"] = _promote_terms(
        block.setdefault("document_terms", []),
        CKM_DOCUMENT_TERMS,
    )
    for workstream in ("busca2a", "busca2b"):
        _promote_block_for_workstream(workstream, "cardiometabolic_precision", 6)
