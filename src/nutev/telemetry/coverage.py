"""Lost-coverage recorder: classified failures instead of silent ``pass``.

A :class:`CoverageLog` accumulates failure events — each with a stable error
code, the component/stage where it happened, whether it is recoverable, any
fallback used and the coverage impact — and writes an auditable report
(``coverage_loss.csv`` / ``coverage_loss.json``). This makes "the pipeline kept
going" honest: what was lost is counted, not hidden.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

from nutev.errors import NutEVError


@dataclass
class CoverageEvent:
    code: str
    component: str
    stage: str = ""
    reason: str = ""
    provider: str = ""
    query: str = ""
    recoverable: bool = True
    attempt: int = 0
    fallback_used: str = ""
    impact: str = ""


@dataclass
class CoverageLog:
    """Collects classified failures during a run."""

    events: list[CoverageEvent] = field(default_factory=list)

    def record(
        self,
        *,
        code: str,
        component: str,
        stage: str = "",
        reason: str = "",
        provider: str = "",
        query: str = "",
        recoverable: bool = True,
        attempt: int = 0,
        fallback_used: str = "",
        impact: str = "",
    ) -> None:
        self.events.append(CoverageEvent(
            code=code, component=component, stage=stage, reason=reason,
            provider=provider, query=query, recoverable=recoverable,
            attempt=attempt, fallback_used=fallback_used, impact=impact,
        ))

    def record_error(self, error: NutEVError, *, component: str, impact: str = "") -> None:
        """Record a typed NutEVError, carrying its classification."""
        self.record(
            code=error.code, component=component, stage=error.stage, reason=error.message,
            provider=error.provider, query=error.query, recoverable=error.recoverable,
            attempt=error.attempt, fallback_used=error.fallback_used,
            impact=impact or error.coverage_impact,
        )

    def record_exception(
        self, exc: Exception, *, code: str, component: str, stage: str = "", impact: str = "",
    ) -> None:
        """Record a generic exception, classifying it under ``code``."""
        if isinstance(exc, NutEVError):
            self.record_error(exc, component=component, impact=impact)
            return
        self.record(code=code, component=component, stage=stage,
                    reason=f"{type(exc).__name__}: {exc}", impact=impact)

    def is_empty(self) -> bool:
        return not self.events

    def rows(self) -> list[dict]:
        return [asdict(e) for e in self.events]

    def summary(self) -> dict:
        by_code = Counter(e.code for e in self.events)
        by_component = Counter(e.component for e in self.events)
        return {
            "total_events": len(self.events),
            "recoverable": sum(1 for e in self.events if e.recoverable),
            "unrecoverable": sum(1 for e in self.events if not e.recoverable),
            "by_code": dict(by_code),
            "by_component": dict(by_component),
        }


def write_coverage_report(log: CoverageLog, out_dir: str | Path) -> dict:
    """Write coverage_loss.csv + coverage_loss.json; return the summary."""
    from nutev.export.metadata_tables import write_simple_csv

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_simple_csv(log.rows(), out / "coverage_loss.csv")
    summary = log.summary()
    (out / "coverage_loss.json").write_text(
        json.dumps({"summary": summary, "events": log.rows()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary
