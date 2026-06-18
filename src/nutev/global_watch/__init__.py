from __future__ import annotations

from typing import Any

from nutev.global_watch.watch_precision_extensions import apply_watch_precision_extensions

apply_watch_precision_extensions()

__all__ = ["run_global_watch", "apply_watch_precision_extensions"]


def __getattr__(name: str) -> Any:
    if name == "run_global_watch":
        from nutev.global_watch.watch_pipeline import run_global_watch

        return run_global_watch
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")