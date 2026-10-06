"""Hosted search: turn a free-text question into a reviewable advanced strategy.

Audit finding A1 (docs/SEARCH_KEYWORD_AUDIT_2026-10.md): the quick search sends the raw
question to every source. This module does not change that path. On request it runs the
deterministic question planner (the one the Open Evidence Explorer uses) and projects
the enabled blocks into the advanced-search schema, so the form can be filled for the
person to review. Nothing is executed here: no network, no persistence, no ranking.
"""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from nutev.search.question_planner import (  # noqa: E402
    MAX_QUESTION_LENGTH,
    load_query_vocabulary,
    plan_question,
    to_review_strategy,
)
from query_compiler import normalize_strategy  # noqa: E402

FRAMEWORK = "PICO"


@lru_cache(maxsize=1)
def _vocabulary() -> dict[str, Any]:
    return load_query_vocabulary(REPO_ROOT / "config")


def interpret_question(question: object, *, current_year: int | None = None) -> dict[str, Any]:
    text = " ".join(str(question or "").split())
    if not text:
        raise ValueError("A pergunta de busca não pode ficar vazia.")
    if len(text) > MAX_QUESTION_LENGTH:
        raise ValueError(f"A pergunta deve ter no máximo {MAX_QUESTION_LENGTH} caracteres.")
    vocabulary = _vocabulary()
    plan = plan_question(text, vocabulary, current_year=current_year or date.today().year)
    strategy = None
    if plan["mode"] != "manual":
        strategy = to_review_strategy(plan, framework=FRAMEWORK)
        if strategy is not None:
            # Same validation the advanced search applies before compiling.
            normalize_strategy(strategy)
    return {
        "mode": "question_plan",
        "executed": False,
        "planner_version": plan["planner_version"],
        "vocabulary_version": plan["vocabulary_version"],
        "vocabulary_review_status": vocabulary.get("review_status"),
        "question": plan["question"],
        "plan_mode": plan["mode"],
        "strategy": strategy,
        "blocks": [
            {
                "label_pt": block["label_pt"],
                "label_en": block["label_en"],
                "role": block["role"],
                "enabled": bool(block["enabled"]),
                "source": block["source"],
            }
            for block in plan["blocks"]
        ],
        "year_from": plan["year_from"],
        "year_to": plan["year_to"],
        "dropped_terms": list(plan["dropped_terms"]),
        "warnings": [warning["code"] for warning in plan["warnings"]],
    }
