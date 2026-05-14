from __future__ import annotations


def manifest_sources(manifest: dict, workstream: str) -> list[dict]:
    sources = manifest.get("workstreams", {}).get(workstream, [])
    return [{"source": "official", "title": s.get("name"), "url": s.get("url"), "authority": s.get("authority", 1)} for s in sources]
