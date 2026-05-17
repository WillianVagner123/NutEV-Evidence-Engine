from __future__ import annotations

WORKSTREAM_ALIASES = {
    "a3": "artigo3_framework",
    "article3": "artigo3_framework",
}


def _dedupe_sources(sources: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique_sources: list[dict] = []
    for source in sources:
        url = (source.get("url") or "").strip().lower()
        title = (source.get("name") or source.get("title") or "").strip().lower()
        key = url or title
        if not key or key in seen:
            continue
        seen.add(key)
        unique_sources.append(source)
    return unique_sources


def manifest_sources(manifest: dict, workstream: str) -> list[dict]:
    ws = WORKSTREAM_ALIASES.get(workstream, workstream)
    workstreams = manifest.get("workstreams", {})
    sources = workstreams.get(ws, [])
    if ws != workstream:
        sources = _dedupe_sources(sources + workstreams.get(workstream, []))

    return [
        {
            "source": "official",
            "title": source.get("name"),
            "url": source.get("url"),
            "authority": source.get("authority", 1),
        }
        for source in sources
    ]