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
            "implementation research",
            "implementation strategy",
            "implementation outcomes",
            "implementation fidelity",
            "knowledge translation",
            "implementation framework",
            "implementation process",
            "implementation facilitation",
            "implementation support",
            "implementation barrier",
            "implementation facilitator",
            "acceptability",
            "feasibility",
            "barriers",
            "facilitators",
            "barriers and facilitators",
            "real-world implementation",
            "pragmatic implementation",
            "adoption",
            "reach",
            "sustainability",
            "dissemination",
            "scale-up",
            "scale out",
            "RE-AIM",
            "CFIR",
            "normalization process theory",
            "hybrid effectiveness implementation",
            "implementation study",
            "implementation trial",
            "practice facilitation",
            "quality improvement",
            "care delivery",
            "service delivery",
            "program implementation",
            "clinical pathway",
            "care pathway",
            "health coaching",
            "nutrition counseling",
            "nutrition counselling",
        ],
        "document_terms": [
            "implementation study",
            "implementation trial",
            "implementation evaluation",
            "process evaluation",
            "mixed methods study",
            "real-world evidence",
            "dissemination study",
            "hybrid type 1",
            "hybrid type 2",
            "hybrid type 3",
            "quality improvement study",
            "clinical pathway",
            "care pathway",
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
            "dietary maintenance",
            "diet quality",
            "healthy eating index",
            "persistence",
            "engagement",
            "retention",
            "dropout",
            "attrition",
            "behavioral maintenance",
            "self-monitoring",
            "dietary self-monitoring",
            "self management",
            "relapse prevention",
            "dietary counseling",
            "dietary counselling",
        ],
        "document_terms": [
            "adherence intervention",
            "maintenance trial",
            "behavior change trial",
            "longitudinal study",
            "adherence study",
        ],
    },
    "food_literacy_agency": {
        "terms": [
            "food literacy",
            "nutrition literacy",
            "food and nutrition literacy",
            "health literacy",
            "food agency",
            "food skills",
            "culinary skills",
            "cooking skills",
            "cooking confidence",
            "home cooking",
            "meal preparation",
            "meal planning",
            "food label",
            "nutrition label",
            "label reading",
            "food choice",
            "self-efficacy",
            "patient activation",
            "empowerment",
            "nutrition education",
            "culinary medicine",
        ],
        "document_terms": [
            "questionnaire validation",
            "scale development",
            "psychometric validation",
            "survey instrument",
            "food literacy instrument",
            "culinary skills instrument",
            "cooking confidence scale",
            "meal planning questionnaire",
        ],
    },
    "commensality_context": {
        "terms": [
            "commensality",
            "comensalidade",
            "shared meals",
            "family meals",
            "meal context",
            "eating context",
            "social eating",
            "eat together",
            "meal sharing",
            "communal eating",
            "mealtime routine",
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
            "nutrition security",
            "food insecurity",
            "food desert",
            "food swamp",
            "social determinants of health",
            "socioeconomic status",
            "access to healthy food",
            "healthy food access",
            "affordability",
            "cultural adaptation",
            "underserved populations",
            "low-income",
            "rural health",
            "community health worker",
            "primary care",
            "racial disparities",
            "ethnic disparities",
        ],
        "document_terms": [
            "equity-focused intervention",
            "community-based intervention",
            "implementation study",
            "policy evaluation",
            "community trial",
        ],
    },
    "evidence_synthesis": {
        "terms": [
            "systematic review",
            "meta-analysis",
            "meta analysis",
            "network meta-analysis",
            "network meta analysis",
            "umbrella review",
            "overview of reviews",
            "review of reviews",
            "scoping review",
            "integrative review",
            "living systematic review",
            "rapid review",
        ],
        "document_terms": [
            "systematic review",
            "meta-analysis",
            "meta analysis",
            "network meta-analysis",
            "network meta analysis",
            "umbrella review",
            "overview of reviews",
            "review of reviews",
            "living systematic review",
            "rapid review",
            "practice guideline",
            "guideline update",
            "consensus statement",
            "scientific statement",
            "position statement",
            "position paper",
            "practice guidance",
            "practice advisory",
            "guidance statement",
            "joint statement",
        ],
    },
    "lifestyle_nutrition_patterns": {
        "terms": [
            "lifestyle medicine",
            "lifestyle intervention",
            "lifestyle modification",
            "therapeutic lifestyle changes",
            "medical nutrition therapy",
            "nutrition care",
            "healthy eating pattern",
            "diet quality",
            "dietary pattern",
            "mediterranean diet",
            "mediterranean dietary pattern",
            "dash diet",
            "dietary approaches to stop hypertension",
            "mind diet",
            "plant-based diet",
            "plant based diet",
            "whole-food plant-based",
            "whole food plant based",
            "portfolio diet",
            "nordic diet",
            "new nordic diet",
            "eat-lancet",
            "planetary health diet",
        ],
        "document_terms": [
            "dietary guideline",
            "food-based dietary guideline",
            "clinical practice guideline",
            "practice guideline",
            "scientific statement",
            "systematic review",
            "umbrella review",
        ],
    },
}

WORKSTREAM_SEMANTIC_PRIORITIES: dict[str, list[tuple[str, int]]] = {
    "busca1": [
        ("food_literacy_agency", 5),
        ("commensality_context", 5),
        ("lifestyle_nutrition_patterns", 5),
        ("implementation_science", 4),
        ("evidence_synthesis", 4),
        ("adherence_persistence", 3),
        ("equity_access", 3),
    ],
    "busca2a": [
        ("implementation_science", 5),
        ("evidence_synthesis", 5),
        ("adherence_persistence", 4),
        ("equity_access", 4),
        ("lifestyle_nutrition_patterns", 4),
        ("food_literacy_agency", 2),
        ("commensality_context", 1),
    ],
    "busca2b": [
        ("implementation_science", 5),
        ("adherence_persistence", 5),
        ("evidence_synthesis", 5),
        ("lifestyle_nutrition_patterns", 5),
        ("food_literacy_agency", 4),
        ("equity_access", 3),
        ("commensality_context", 2),
    ],
    "artigo3_framework": [
        ("food_literacy_agency", 5),
        ("commensality_context", 5),
        ("implementation_science", 4),
        ("adherence_persistence", 4),
        ("evidence_synthesis", 3),
        ("lifestyle_nutrition_patterns", 3),
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
    terms: list[str] = []
    for block_name, priority in WORKSTREAM_SEMANTIC_PRIORITIES.get(ws_key, []):
        if priority < min_priority:
            continue
        block = SEMANTIC_RESEARCH_BLOCKS.get(block_name, {})
        terms.extend(block.get(field, []))
    return _uniq(terms)