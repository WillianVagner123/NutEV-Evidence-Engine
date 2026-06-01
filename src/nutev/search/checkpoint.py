from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def query_hash(provider: str, workstream: str, query: str) -> str:
    payload = f"{provider}\0{workstream}\0{query}".encode("utf-8")
    return hashlib.sha1(payload).hexdigest()[:16]  # noqa: S324


def checkpoint_path(base_dir: Path, provider: str, workstream: str, query: str) -> Path:
    return base_dir / provider / f"{query_hash(provider, workstream, query)}.json"


def load_checkpoint(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_checkpoint(path: Path, data: dict[str, Any]) -> None:
    payload = dict(data)
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
