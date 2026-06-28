from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES

CATEGORY_TERM_EXTENSIONS: dict[str, list[str]] = {
    "guidelines_consensus": [
        "diabetes remission guideline",
        "type 2 diabetes remission guideline",
        "diabetes remission consensus",
        "diabetes remission consensus report",
        "type 2 diabetes remission consensus",
        "weight loss maintenance guideline",
        "weight regain prevention guideline",
    ],
    "lifestyle_medicine": [
        "diabetes remission maintenance",
        "type 2 diabetes remission program",
        "type 2 diabetes remission programme",
        "remission maintenance",
        "total diet replacement program",
        "total diet replacement programme",
        "very low energy diet program",
        "very low energy diet programme",
    ],
    "obesity_cardiometabolic": [
        "glycemic remission",
        "glycaemic remission",
        "diabetes remission maintenance",
        "type 2 diabetes remission maintenance",
        "remission maintenance",
        "weight loss maintenance intervention",
        "weight regain prevention intervention",
        "total diet replacement",
        "very low energy diet",
    ],
    "implementation_behavior": [
        "diabetes remission maintenance",
        "type 2 diabetes remission maintenance",
        "remission maintenance",
        "total diet replacement intervention",
        "very low energy diet intervention",
        "weight regain prevention intervention",
    ],
}


def _extend_unique(target: list[str], additions: list[str]) -> None:
    seen = {term.lower() for term in target}
    for term in additions:
        normalized = term.strip()
        if not normalized or normalized.lower() in seen:
            continue
        target.append(normalized)
        seen.add(normalized.lower())


def apply_metabolic_remission_extensions() -> None:
    for category, terms in CATEGORY_TERM_EXTENSIONS.items():
        _extend_unique(WATCH_CATEGORIES.setdefault(category, []), terms)


__all__ = ["apply_metabolic_remission_extensions"]
