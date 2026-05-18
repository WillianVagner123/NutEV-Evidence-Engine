from __future__ import annotations

WORKSTREAM_ALIASES = {
    "a3": "artigo3_framework",
    "article3": "artigo3_framework",
}

SemanticBlock = dict[str, list[str]]

SEMANTIC_RESEARCH_BLOCKS: dict[str, SemanticBlock] = {
    "implementation_science": {
        "terms": [
            "implementation science",
            "process evaluation",
            "knowledge translation",
            "implementation framework",
            "implementation strategy",
            "implementation outcomes",
            "implementation fidelity",
            "practice facilitation",
            "real-world implementation",
            "pragmatic implementation",
            "scale-up",
            "RE-AIM",
            "CFIR",
            "normalization process theory",
            "hybrid effectiveness implementation",
            "implementation study",
            "implementation trial",
            "implementation barriers",
            "implementation facilitators",
            "health coaching",
            "nutrition counseling",
            "nutrition counselling",
        ],
        "document_terms": [
            "implementation study",
            "implementation trial",
            "process evaluation",
            "mixed methods study",
            "real-world evidence",
        ],
    },
    "adherence_persistence": {
        "terms": [
            "adherence",
            "dietary adherence",
            "treatment adherence",
            "long-term adherence",
            "maintenance",
            "weight maintenance",
            "persistence",
            "engagement",
            "retention",
            "dropout",
            "attrition",
            "behavioral maintenance",
            "self-monitoring",
            "relapse prevention",
            "dietary counseling",
            "dietary counselling",
        ],
        "document_terms": [
            "adherence intervention",
            "maintenance trial",
            "behavior change trial",
            "longitudinal study",
        ],
    },
    "food_literacy_agency": {
        "terms": [
            "food literacy",
            "food environment",
            "nutrition literacy",
            "nutrition label",
            "health literacy",
            "front-of-pack labeling",
            "food agency",
            "food skills",
            "shopping skills",
            "culinary skills",
            "cooking skills",
            "cooking confidence",
            "meal planning",
            "label reading",
            "food choice",
            "self-efficacy",
            "patient activation",
            "empowerment",
            "nutrition education",
            "food and nutrition literacy",
        ],
        "document_terms": [
            "questionnaire validation",
            "scale development",
            "psychometric validation",
            "survey instrument",
        ],
    },
    "commensality_context": {
        "terms": [
            "commensality",
            "shared meals",
            "family meals",
            "meal context",
            "eating context",
            "social eating",
            "food environment",
            "household food practices",
            "cultural food practices",
            "food culture",
            "meal routine",
        ],
        "document_terms": [
            "qualitative study",
            "mixed methods study",
            "ethnographic study",
            "observational study",
        ],
    },
    "equity_access": {
        "terms": [
            "health equity",
            "food insecurity",
            "social determinants of health",
            "socioeconomic status",
            "access to healthy food",
            "affordability",
            "cultural adaptation",
            "underserved populations",
            "low-income",
            "racial disparities",
            "ethnic disparities",
        ],
        "document_terms": [
            "equity-focused intervention",
            "community-based intervention",
            "implementation study",
            "policy evaluation",
        ],
    },
}

WORKSTREAM_SEMANTIC_PRIORITIES: dict[str, list[tuple[str, int]]] = {
    "busca1": [
        ("food_literacy_agency", 5),
        ("commensality_context", 5),
        ("implementation_science", 4),
        ("adherence_persistence", 3),
        ("equity_access", 3),
    ],
    "busca2a": [
        ("implementation_science", 5),
        ("adherence_persistence", 4),
        ("equity_access", 4),
        ("food_literacy_agency", 2),
        ("commensality_context", 1),
    ],
    "busca2b": [
        ("adherence_persistence", 5),
        ("implementation_science", 5),
        ("food_literacy_agency", 4),
        ("equity_access", 3),
        ("commensality_context", 2),
    ],
    "artigo3_framework": [
        ("food_literacy_agency", 5),
        ("commensality_context", 5),
        ("implementation_science", 4),
        ("adherence_persistence", 4),
        ("equity_access", 3),
    ],
}


def _canonical_workstream(workstream: str) -> str:
    return WORKSTREAM_ALIASES.get(workstream, workstream)


def _uniq(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        value = str(item).strip()
        if not value:
            continue
        low = value.lower()
        if low in seen:
            continue
        seen.add(low)
        out.append(value)
    return out


def _interleave_groups(groups: list[list[str]]) -> list[str]:
    clean_groups = [_uniq(group) for group in groups if group]
    if not clean_groups:
        return []

    out: list[str] = []
    seen: set[str] = set()
    depth = 0
    while True:
        progressed = False
        for group in clean_groups:
            if depth >= len(group):
                continue
            term = group[depth]
            key = term.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(term)
            progressed = True
        if not progressed:
            break
        depth += 1
    return out


def semantic_block_names(workstream: str) -> list[str]:
    ws_key = _canonical_workstream(workstream)
    return [name for name, _ in WORKSTREAM_SEMANTIC_PRIORITIES.get(ws_key, [])]


def prioritized_semantic_blocks(workstream: str) -> list[dict[str, int | str]]:
    ws_key = _canonical_workstream(workstream)
    return [
        {"name": name, "priority": priority}
        for name, priority in WORKSTREAM_SEMANTIC_PRIORITIES.get(ws_key, [])
    ]


def semantic_terms(
    workstream: str,
    *,
    field: str = "terms",
    min_priority: int = 1,
) -> list[str]:
    ws_key = _canonical_workstream(workstream)
    term_groups: list[list[str]] = []
    for block_name, priority in WORKSTREAM_SEMANTIC_PRIORITIES.get(ws_key, []):
        if priority < min_priority:
            continue
        block = SEMANTIC_RESEARCH_BLOCKS.get(block_name, {})
        term_groups.append(block.get(field, []))
    return _interleave_groups(term_groups)
