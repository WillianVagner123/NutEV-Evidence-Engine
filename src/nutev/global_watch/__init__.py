from __future__ import annotations

from typing import Any

from nutev.global_watch.group_visit_extensions import apply_group_visit_watch_extensions
from nutev.global_watch.watch_extensions import apply_watch_taxonomy_extensions

apply_watch_taxonomy_extensions()
apply_group_visit_watch_extensions()

__all__ = ["run_global_watch"]


def __getattr__(name: str) -> Any:
    if name == "run_global_watch":
        from nutev.global_watch.watch_pipeline import run_global_watch

        return run_global_watch
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
