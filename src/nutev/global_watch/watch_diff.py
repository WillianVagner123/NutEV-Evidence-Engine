from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_seen_items(path: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_seen_items(path: Path, items: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def mark_new_items(
    candidates: list[dict[str, Any]],
    seen_items: dict[str, Any],
) -> list[dict[str, Any]]:
    for candidate in candidates:
        candidate["is_new"] = candidate.get("document_id") not in seen_items
    return candidates


def update_seen_items(
    candidates: list[dict[str, Any]],
    seen_items: dict[str, Any],
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).date().isoformat()
    out = dict(seen_items)
    for candidate in candidates:
        document_id = candidate.get("document_id")
        if not document_id:
            continue
        previous = out.get(document_id, {})
        out[document_id] = {
            "document_id": document_id,
            "first_seen_date": previous.get("first_seen_date", now),
            "last_seen_date": now,
            "title": candidate.get("title", ""),
            "doi": candidate.get("doi", ""),
            "url": candidate.get("url", ""),
            "source_provider": candidate.get("source_provider", ""),
            "category": candidate.get("category", ""),
            "relevance_score": candidate.get("relevance_score", 0),
            "last_status": candidate.get("download_status", "metadata_only"),
        }
    return out
