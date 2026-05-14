from __future__ import annotations

WORKSTREAM_ALIASES = {
    "a3": "artigo3_framework",
    "article3": "artigo3_framework",
}


def manifest_sources(manifest: dict, workstream: str) -> list[dict]:
    ws = WORKSTREAM_ALIASES.get(workstream, workstream)
    sources = manifest.get("workstreams", {}).get(ws, [])
    return [
        {
            "source": "official",
            "title": s.get("name"),
            "url": s.get("url"),
            "authority": s.get("authority", 1),
        }
        for s in sources
    ]