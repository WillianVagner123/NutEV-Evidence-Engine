from __future__ import annotations

from collections.abc import Iterable

from nutev.engine.ids import make_document_id
from nutev.global_watch.watch_config import MODE_LIMITS, WATCH_CATEGORIES

BASE_CONTEXT_TERMS = [
    "nutrition",
    "diet",
    "food",
    "obesity",
    "cardiometabolic",
]

EVIDENCE_SYNTHESIS_TERMS = [
    "systematic review",
    "meta-analysis",
    "meta analysis",
    "network meta-analysis",
    "network meta analysis",
    "umbrella review",
    "scoping review",
    "integrative review",
    "rapid review",
    "living systematic review",
    "overview of reviews",
    "review of reviews",
]

CATEGORY_CONTEXT_TERMS = {
    "guidelines_consensus": [
        "dietary guideline",
        "dietary pattern",
        "lifestyle medicine",
        "practice guideline",
        "position paper",
        "food-based dietary guideline",
        "food based dietary guideline",
        "dietary guidance",
        "consensus report",
        "practice advisory",
        "practice guidance",
        "guidance statement",
        "joint statement",
        "joint guideline",
        "expert consensus",
        "clinical guidance",
        "practice recommendation",
        "food guide",
        "nutrition guideline",
        "standards of care",
        "clinical pathway",
        "care pathway",
        "clinical decision pathway",
        "decision pathway",
        "living guideline",
        *EVIDENCE_SYNTHESIS_TERMS,
    ],
    "lifestyle_medicine": [
        "food literacy",
        "culinary medicine",
        "culinary nutrition",
        "teaching kitchen",
        "teaching kitchens",
        "meal planning",
        "healthy lifestyle",
        "lifestyle counseling",
        "lifestyle counselling",
        "behavioral lifestyle intervention",
        "medical nutrition therapy",
        "food is medicine",
        "produce prescription",
        "produce prescriptions",
        "produce prescription program",
        "medically tailored meal",
        "medically tailored meals",
        "medically tailored grocery",
        "medically tailored groceries",
        "nutrition counseling",
        "nutrition counselling",
        "nutrition care",
        "registered dietitian",
        "registered dietitian nutritionist",
        "dietitian-led",
        "dietitian led",
    ],
    "obesity_cardiometabolic": [
        "dietary pattern",
        "lifestyle medicine",
        "implementation",
        "adherence",
        "prediabetes",
        "insulin resistance",
        "dyslipidaemia",
        "hyperlipidemia",
        "hyperlipidaemia",
        "hypercholesterolemia",
        "hypercholesterolaemia",
        "steatotic liver disease",
        "metabolic dysfunction-associated steatotic liver disease",
        "weight management",
        "adiposity",
        "blood pressure",
        "fatty liver",
        *EVIDENCE_SYNTHESIS_TERMS,
    ],
    "diet_patterns": [
        "type 2 diabetes",
        "hypertension",
        "implementation",
        "adherence",
        "insulin resistance",
        "steatotic liver disease",
        "mediterranean diet",
        "mediterranean dietary pattern",
        "dash",
        "dietary approaches to stop hypertension",
        "mind diet",
        "plant-based diet",
        "plant based diet",
        "whole-food plant-based",
        "portfolio diet",
        "nordic diet",
        "new nordic diet",
        "eat-lancet",
        "planetary health diet",
        *EVIDENCE_SYNTHESIS_TERMS,
    ],
    "implementation_behavior": [
        "lifestyle medicine",
        "food literacy",
        "culinary medicine",
        "culinary nutrition",
        "teaching kitchen",
        "teaching kitchens",
        "implementation science",
        "implementation research",
        "knowledge translation",
        "dietary adherence",
        "treatment adherence",
        "self-efficacy",
        "self-monitoring",
        "self-management",
        "self management",
        "self-management support",
        "meal planning",
        "implementation strategy",
        "implementation outcomes",
        "implementation fidelity",
        "implementation facilitation",
        "implementation support",
        "implementation barrier",
        "implementation barriers",
        "implementation facilitator",
        "implementation facilitators",
        "implementation determinant",
        "implementation determinants",
        "process evaluation",
        "shared decision making",
        "behavior change technique",
        "barriers and facilitators",
        "behavioral lifestyle intervention",
        "behavioral weight loss",
        "weight loss maintenance",
        "goal setting",
        "social support",
        "food access",
        "food is medicine",
        "produce prescription",
        "produce prescriptions",
        "produce prescription program",
        "medically tailored meal",
        "medically tailored meals",
        "medically tailored grocery",
        "medically tailored groceries",
        "sustainability",
        "dissemination",
        "scale-up",
        "scale up",
        "adoption",
        "reach",
        "maintenance",
        "registered dietitian",
        "registered dietitian nutritionist",
        "dietitian-led",
        "dietitian led",
        *EVIDENCE_SYNTHESIS_TERMS,
    ],
    "food_literacy_culinary_commensality": [
        "lifestyle medicine",
        "behavior change",
        "adherence",
        "food environment",
        "nutrition education",
        "food and nutrition literacy",
        "nutrition literacy",
        "food agency",
        "home cooking",
        "meal preparation",
        "cooking confidence",
        "cooking skills",
        "food skills",
        "culinary nutrition",
        "teaching kitchen",
        "teaching kitchens",
        "food label",
        "food access",
        "commensality",
        "shared meals",
        "family meals",
        "social eating",
        "eat together",
    ],
    "frameworks_instruments": [
        "lifestyle medicine",
        "food literacy",
        "culinary medicine",
        "commensality",
        "psychometric validation",
        "scale development",
        "lifestyle medicine competencies",
    ],
}

QUICK_MODE_SEED_GROUPS = {
    "guidelines_consensus": [
        [
            "clinical practice guideline",
            "guideline",
            "guidelines",
            "guideline update",
            "dietary guidelines",
            "food-based dietary guidelines",
            "diretriz",
            "recomendações",
        ],
        [
            "consensus",
            "consensus statement",
            "consensus report",
            "expert consensus",
            "consenso",
            "standards of care",
        ],
        [
            "scientific statement",
            "position statement",
            "position paper",
            "practice advisory",
            "practice guidance",
            "guidance statement",
            "joint statement",
            "joint guideline",
            "clinical guidance",
            "recommendation",
            "declaração científica",
            "clinical pathway",
            "care pathway",
            "clinical decision pathway",
            "decision pathway",
            "living guideline",
        ],
    ],
    "lifestyle_medicine": [
        [
            "lifestyle medicine",
            "lifestyle medicine nutrition",
            "medical nutrition therapy",
            "medicina do estilo de vida",
        ],
        [
            "lifestyle intervention",
            "lifestyle modification",
            "therapeutic lifestyle changes",
            "nutrition counseling",
            "nutrition counselling",
            "food is medicine",
            "produce prescription",
            "produce prescriptions",
        ],
        [
            "healthy lifestyle",
            "lifestyle counseling",
            "lifestyle counselling",
            "nutrition care",
            "estilo de vida saudavel",
            "medically tailored meal",
            "medically tailored meals",
            "medically tailored grocery",
            "medically tailored groceries",
        ],
    ],
    "obesity_cardiometabolic": [
        [
            "obesity",
            "clinical obesity",
            "overweight",
            "adiposity",
            "weight management",
        ],
        [
            "cardiometabolic risk",
            "metabolic syndrome",
            "type 2 diabetes",
            "prediabetes",
            "insulin resistance",
        ],
        [
            "hypertension",
            "dyslipidemia",
            "dyslipidaemia",
            "hyperlipidemia",
            "hyperlipidaemia",
            "hypercholesterolemia",
            "hypercholesterolaemia",
            "MASLD",
            "NAFLD",
            "MAFLD",
            "MASH",
            "NASH",
            "steatotic liver disease",
            "metabolic dysfunction-associated fatty liver disease",
            "systematic review",
            "meta-analysis",
            "umbrella review",
        ],
    ],
    "diet_patterns": [
        [
            "Mediterranean diet",
            "Mediterranean dietary pattern",
            "DASH",
            "Dietary Approaches to Stop Hypertension",
            "MIND diet",
        ],
        [
            "plant-based diet",
            "plant based diet",
            "vegetarian diet",
            "vegan diet",
            "whole-food plant-based",
            "whole food plant based",
        ],
        [
            "Eat-Lancet",
            "planetary health diet",
            "Portfolio diet",
            "Nordic diet",
            "New Nordic diet",
            "systematic review",
            "network meta-analysis",
            "umbrella review",
            "rapid review",
            "living systematic review",
        ],
    ],
    "implementation_behavior": [
        [
            "adherence",
            "compliance",
            "acceptability",
            "feasibility",
            "self-monitoring",
            "dietary adherence",
            "treatment adherence",
            "self-management",
            "maintenance",
            "weight loss maintenance",
        ],
        [
            "implementation",
            "implementation science",
            "implementation research",
            "implementation fidelity",
            "implementation facilitation",
            "implementation support",
            "implementation outcomes",
            "implementation determinants",
            "implementation barriers",
            "implementation facilitators",
            "process evaluation",
            "practice facilitation",
            "health coaching",
            "RE-AIM",
            "CFIR",
            "barriers and facilitators",
            "lifestyle counseling",
            "lifestyle counselling",
            "self-management support",
            "shared decision making",
        ],
        [
            "behavior change",
            "behavior change technique",
            "motivational interviewing",
            "social support",
            "food agency",
            "meal planning",
            "registered dietitian",
            "registered dietitian nutritionist",
            "dietitian-led intervention",
            "dietitian led intervention",
            "teaching kitchen",
            "teaching kitchens",
            "culinary nutrition",
            "food is medicine",
            "produce prescription",
            "produce prescriptions",
            "medically tailored meals",
            "medically tailored groceries",
            "sustainability",
            "dissemination",
            "scale-up",
            "adoption",
            "reach",
            "systematic review",
            "scoping review",
            "rapid review",
        ],
    ],
    "food_literacy_culinary_commensality": [
        [
            "food literacy",
            "food and nutrition literacy",
            "nutrition literacy",
            "health literacy",
        ],
        [
            "culinary medicine",
            "culinary nutrition",
            "teaching kitchen",
            "teaching kitchens",
            "cooking skills",
            "food skills",
            "food agency",
            "home cooking",
            "meal planning",
            "meal preparation",
            "cooking confidence",
        ],
        [
            "food environment",
            "food access",
            "shared meals",
            "family meals",
            "social eating",
            "eat together",
            "commensality",
            "comensalidade",
        ],
    ],
    "frameworks_instruments": [
        [
            "framework",
            "behavior change framework",
            "lifestyle medicine competencies",
        ],
        [
            "questionnaire",
            "instrument",
            "survey instrument",
            "adherence scale",
            "food literacy instrument",
            "culinary skills instrument",
        ],
        [
            "psychometric validation",
            "psychometric study",
            "scale development",
            "questionnaire validation",
            "validation study",
        ],
    ],
}

HIGH_PRIORITY_MARKERS = (
    "guideline",
    "consensus",
    "statement",
    "recommendation",
    "position paper",
    "standards of care",
    "clinical pathway",
    "care pathway",
    "clinical decision pathway",
    "decision pathway",
)


def _dedupe_terms(terms: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique_terms: list[str] = []
    for term in terms:
        value = str(term).strip()
        if not value:
            continue
        lowered = value.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique_terms.append(value)
    return unique_terms


def _quote_term(term: str) -> str:
    return f'"{term.strip()}"'


def _or_clause(terms: Iterable[str]) -> str:
    quoted_terms = [_quote_term(term) for term in _dedupe_terms(terms)]
    if not quoted_terms:
        return ""
    if len(quoted_terms) == 1:
        return quoted_terms[0]
    return "(" + " OR ".join(quoted_terms) + ")"


def _build_context_terms(category: str) -> list[str]:
    return _dedupe_terms(
        [
            *BASE_CONTEXT_TERMS,
            *CATEGORY_CONTEXT_TERMS.get(category, []),
        ]
    )


def _priority_for_term(term: str | Iterable[str]) -> int:
    candidates = [term] if isinstance(term, str) else list(term)
    lowered_candidates = [str(value).lower() for value in candidates]
    if any(
        marker in candidate
        for candidate in lowered_candidates
        for marker in HIGH_PRIORITY_MARKERS
    ):
        return 1
    return 2


def _mode_terms(category: str, mode: str) -> list[str | list[str]]:
    if mode == "quick" and category in QUICK_MODE_SEED_GROUPS:
        return QUICK_MODE_SEED_GROUPS[category]
    return WATCH_CATEGORIES.get(category, [])


def _term_clause(term: str | Iterable[str]) -> str:
    if isinstance(term, str):
        return _quote_term(term)
    return _or_clause(term)


def _build_category_queries(
    category: str,
    since_days: int,
    mode: str,
) -> list[dict[str, object]]:
    context_clause = _or_clause(_build_context_terms(category))
    queries: list[dict[str, object]] = []
    for term in _mode_terms(category, mode)[: MODE_LIMITS.get(mode, 6)]:
        term_clause = _term_clause(term)
        query = f"({term_clause})"
        if context_clause:
            query = f"{query} AND {context_clause}"
        queries.append(
            {
                "query_id": make_document_id(
                    {"title": query, "provider": "watch", "year": since_days}
                ),
                "category": category,
                "query": query,
                "provider_hint": "pubmed",
                "priority": _priority_for_term(term),
                "since_days": since_days,
            }
        )
    return sorted(
        queries,
        key=lambda query: (int(query["priority"]), str(query["query"])),
    )


def _interleave_category_queries(
    category_queries: dict[str, list[dict[str, object]]],
) -> list[dict[str, object]]:
    ordered: list[dict[str, object]] = []
    max_bucket = max((len(bucket) for bucket in category_queries.values()), default=0)
    for index in range(max_bucket):
        for category in category_queries:
            bucket = category_queries.get(category, [])
            if index < len(bucket):
                ordered.append(bucket[index])
    return ordered


def build_watch_queries(
    categories: list[str] | None,
    since_days: int,
    mode: str,
) -> list[dict[str, object]]:
    selected_categories = categories or list(WATCH_CATEGORIES.keys())
    category_queries = {
        category: _build_category_queries(category, since_days, mode)
        for category in selected_categories
    }
    return _interleave_category_queries(category_queries)
