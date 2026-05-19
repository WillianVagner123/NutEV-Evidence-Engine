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
        "guidance statement",
        "policy statement",
        "standard of care",
        "standards of care",
        "expert consensus",
        "clinical guidance",
        "practice recommendation",
        "food guide",
        "nutrition guideline",
    ],
    "lifestyle_medicine": [
        "food literacy",
        "culinary medicine",
        "meal planning",
        "healthy lifestyle",
        "lifestyle counseling",
        "lifestyle counselling",
        "behavioral lifestyle intervention",
    ],
    "obesity_cardiometabolic": [
        "dietary pattern",
        "lifestyle medicine",
        "implementation",
        "adherence",
        "prediabetes",
        "insulin resistance",
        "dyslipidaemia",
        "steatotic liver disease",
        "metabolic dysfunction-associated steatotic liver disease",
        "metabolic dysfunction-associated fatty liver disease",
        "weight management",
        "adiposity",
        "blood pressure",
        "fatty liver",
    ],
    "diet_patterns": [
        "type 2 diabetes",
        "hypertension",
        "implementation",
        "adherence",
        "insulin resistance",
        "steatotic liver disease",
        "mediterranean diet",
        "dash",
        "mind diet",
        "plant-based diet",
        "whole-food plant-based",
        "portfolio diet",
        "nordic diet",
        "eat-lancet",
        "planetary health diet",
    ],
    "implementation_behavior": [
        "lifestyle medicine",
        "food literacy",
        "culinary medicine",
        "implementation science",
        "implementation research",
        "knowledge translation",
        "dietary adherence",
        "self-efficacy",
        "self-monitoring",
        "meal planning",
        "implementation strategy",
        "implementation outcomes",
        "implementation fidelity",
        "implementation facilitation",
        "implementation support",
        "implementation barrier",
        "implementation facilitator",
        "process evaluation",
        "behavior change technique",
        "barriers and facilitators",
        "behavioral lifestyle intervention",
        "behavioral weight loss",
        "goal setting",
        "social support",
        "food access",
        "sustainability",
        "dissemination",
        "scale-up",
        "scale up",
        "adoption",
        "reach",
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
            "standards of care",
            "diretriz",
            "recomendações",
        ],
        [
            "consensus",
            "consensus statement",
            "consensus report",
            "expert consensus",
            "consenso",
        ],
        [
            "scientific statement",
            "position statement",
            "position paper",
            "practice advisory",
            "guidance statement",
            "policy statement",
            "clinical guidance",
            "recommendation",
            "declaração científica",
        ],
    ],
    "lifestyle_medicine": [
        [
            "lifestyle medicine",
            "lifestyle medicine nutrition",
            "medicina do estilo de vida",
        ],
        [
            "lifestyle intervention",
            "lifestyle modification",
            "therapeutic lifestyle changes",
        ],
        [
            "healthy lifestyle",
            "lifestyle counseling",
            "lifestyle counselling",
            "estilo de vida saudavel",
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
            "MASLD",
            "NAFLD",
            "MAFLD",
            "MASH",
            "NASH",
            "steatotic liver disease",
            "metabolic dysfunction-associated fatty liver disease",
        ],
    ],
    "diet_patterns": [
        [
            "Mediterranean diet",
            "DASH",
            "MIND diet",
        ],
        [
            "plant-based diet",
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
        ],
    ],
    "implementation_behavior": [
        [
            "adherence",
            "compliance",
            "acceptability",
            "feasibility",
            "self-monitoring",
        ],
        [
            "implementation",
            "implementation science",
            "implementation research",
            "implementation fidelity",
            "implementation facilitation",
            "implementation support",
            "implementation barrier",
            "implementation facilitator",
            "lifestyle counseling",
            "lifestyle counselling",
        ],
        [
            "behavior change",
            "motivational interviewing",
            "social support",
            "food agency",
            "meal planning",
            "sustainability",
            "dissemination",
            "scale-up",
            "adoption",
            "reach",
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
    "guidance statement",
    "policy statement",
    "standard of care",
    "standards of care",
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


def build_watch_queries(
    categories: list[str] | None,
    since_days: int,
    mode: str,
) -> list[dict[str, object]]:
    selected_categories = categories or list(WATCH_CATEGORIES.keys())
    limit = MODE_LIMITS.get(mode, 6)
    queries: list[dict[str, object]] = []

    for category in selected_categories:
        context_clause = _or_clause(_build_context_terms(category))
        for term in _mode_terms(category, mode)[:limit]:
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
    return queries
