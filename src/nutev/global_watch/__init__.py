from __future__ import annotations

from typing import Any

from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_expansions import apply_watch_expansions

apply_watch_expansions(WATCH_CATEGORIES)

__all__ = ["run_global_watch"]


def __getattr__(name: str) -> Any:
    if name == "run_global_watch":
        from nutev.global_watch.watch_pipeline import run_global_watch

        return run_global_watch
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
