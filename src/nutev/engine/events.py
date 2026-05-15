from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from nutev.engine.enums import EventKind
from nutev.engine.models import RunEvent


DEFAULT_EVENTS_PATH = Path("project_output/07_logs/run_events.jsonl")


def emit_event(run_id: str, stage: str, message: str, event_kind: EventKind = EventKind.progress, **kwargs) -> RunEvent:
    return RunEvent(
        run_id=run_id,
        event_at=datetime.now(timezone.utc),
        event_kind=event_kind,
        stage=stage,
        message=message,
        provider=kwargs.get("provider"),
        host=kwargs.get("host"),
        document_id=kwargs.get("document_id"),
        meta_json=kwargs.get("meta_json", {}),
    )


def write_event(event: RunEvent, path: Path = DEFAULT_EVENTS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=False) + "\n")


def load_events(path: Path = DEFAULT_EVENTS_PATH) -> list[RunEvent]:
    if not path.exists():
        return []
    return [RunEvent.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
