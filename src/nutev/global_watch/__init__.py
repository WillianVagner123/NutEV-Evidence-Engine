from __future__ import annotations

from collections.abc import Iterable
from typing import Any

__all__ = ["run_global_watch"]


def _append_unique_terms(seed_terms: list[str], new_terms: Iterable[str]) -> None:
    seen = {term.lower() for term in seed_terms}
    for term in new_terms:
        value = str(term).strip()
        if not value:
            continue
        lowered = value.lower()
        if lowered in seen:
            continue
        seed_terms.append(value)
        seen.add(lowered)


def _extend_watch_query_terms() -> None:
    from nutev.global_watch import watch_query_builder

    obesity_groups = watch_query_builder.QUICK_MODE_SEED_GROUPS.get(
        "obesity_cardiometabolic", []
    )
    if len(obesity_groups) >= 2:
        _append_unique_terms(
            obesity_groups[0],
            [
                "weight maintenance",
                "weight loss maintenance",
                "weight regain prevention",
                "anti-obesity medication nutrition",
                "obesity pharmacotherapy nutrition care",
                "glp-1 nutrition",
                "glp-1 receptor agonist nutrition",
                "incretin therapy nutrition care",
            ],
        )
        _append_unique_terms(
            obesity_groups[1],
            [
                "type 2 diabetes remission",
                "diabetes remission",
                "remission of type 2 diabetes",
                "diabetes reversal",
            ],
        )

    implementation_groups = watch_query_builder.QUICK_MODE_SEED_GROUPS.get(
        "implementation_behavior", []
    )
    if implementation_groups:
        _append_unique_terms(
            implementation_groups[0],
            [
                "long-term weight loss maintenance",
                "long term weight loss maintenance",
                "weight regain prevention",
                "dietary self-monitoring",
                "dietary self-regulation",
            ],
        )


_extend_watch_query_terms()


def __getattr__(name: str) -> Any:
    if name == "run_global_watch":
        from nutev.global_watch.watch_pipeline import run_global_watch

        return run_global_watch
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
