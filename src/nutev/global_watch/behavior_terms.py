from __future__ import annotations

from collections.abc import Iterable


ADHERENCE_MAINTENANCE_TERMS: tuple[str, ...] = (
    "dietary adherence",
    "treatment adherence",
    "long-term adherence",
    "long term adherence",
    "dietary maintenance",
    "behavioral maintenance",
    "behavioural maintenance",
    "weight loss maintenance",
    "long-term weight loss maintenance",
    "long term weight loss maintenance",
    "weight regain prevention",
    "weight regain management",
    "relapse prevention",
    "lapse management",
    "habit formation",
    "dietary self-monitoring",
    "dietary self regulation",
    "dietary self-regulation",
    "eating self-regulation",
    "self-regulation of eating",
)

IMPLEMENTATION_PRAGMATIC_TERMS: tuple[str, ...] = (
    "pragmatic trial",
    "pragmatic clinical trial",
    "pragmatic randomized trial",
    "pragmatic randomised trial",
    "pragmatic lifestyle intervention",
    "pragmatic nutrition intervention",
    "real-world effectiveness",
    "real world effectiveness",
    "effectiveness-implementation trial",
    "effectiveness implementation trial",
    "implementation-effectiveness trial",
    "implementation effectiveness trial",
    "hybrid effectiveness-implementation trial",
    "hybrid effectiveness implementation trial",
    "program implementation",
    "practice facilitation",
    "quality improvement study",
)

BARRIER_FACILITATOR_TERMS: tuple[str, ...] = (
    "implementation barrier",
    "implementation barriers",
    "implementation facilitator",
    "implementation facilitators",
    "implementation determinant",
    "implementation determinants",
    "barriers and facilitators",
    "acceptability",
    "appropriateness",
    "feasibility",
    "adoption",
    "reach",
    "penetration",
    "sustainment",
    "implementation climate",
    "organizational readiness",
    "readiness for implementation",
)

BEHAVIOR_CHANGE_PLANNING_TERMS: tuple[str, ...] = (
    "action planning",
    "coping planning",
    "goal setting",
    "problem solving",
    "implementation intentions",
    "motivational interviewing",
    "health coaching",
    "self-management support",
    "shared decision making",
    "behavior change technique",
    "behaviour change technique",
    "behavior change techniques",
    "behaviour change techniques",
    "behavior change wheel",
    "behaviour change wheel",
    "capability opportunity motivation behavior",
    "capability opportunity motivation behaviour",
    "COM-B",
)


def _unique_terms(groups: Iterable[Iterable[str]]) -> tuple[str, ...]:
    seen: set[str] = set()
    terms: list[str] = []
    for group in groups:
        for term in group:
            normalized = term.strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            terms.append(normalized)
    return tuple(terms)


def controlled_behavior_terms() -> tuple[str, ...]:
    """Return NutMEV behavior and implementation terms in stable order."""
    return _unique_terms(
        (
            ADHERENCE_MAINTENANCE_TERMS,
            IMPLEMENTATION_PRAGMATIC_TERMS,
            BARRIER_FACILITATOR_TERMS,
            BEHAVIOR_CHANGE_PLANNING_TERMS,
        )
    )
