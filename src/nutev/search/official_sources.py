from __future__ import annotations

WORKSTREAM_ALIASES = {
    "a3": "artigo3_framework",
    "article3": "artigo3_framework",
}


def manifest_sources(manifest: dict, workstream: str) -> list[dict]:
    canonical = WORKSTREAM_ALIASES.get(workstream, workstream)
    workstreams = manifest.get("workstreams", {})
    sources = workstreams.get(canonical, []) or workstreams.get(workstream, [])
    return [
        {
            "source": "official",
            "title": item.get("name"),
            "url": item.get("url"),
            "authority": item.get("authority", 1),
        }
        for item in sources
    ]
