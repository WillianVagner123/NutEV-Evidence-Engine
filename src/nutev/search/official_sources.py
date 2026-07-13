from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

WORKSTREAM_ALIASES = {
    "a3": "artigo3_framework",
    "article3": "artigo3_framework",
}


def load_official_manifest(config_root: Path, include_countries: bool = True) -> dict:
    """Load the base official-source manifest and optionally merge the global
    per-country/region manifest (`official_sources_countries.json`)."""
    def _read(path: Path) -> dict:
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    base = _read(Path(config_root) / "official_sources_manifest.json")
    if include_countries:
        countries = _read(Path(config_root) / "official_sources_countries.json")
        extra_ws = countries.get("workstreams") if isinstance(countries, dict) else None
        if isinstance(extra_ws, dict):
            sw = base.setdefault("workstreams", {})
            for ws_name, extra in extra_ws.items():
                if isinstance(extra, list) and isinstance(sw.get(ws_name, []), list):
                    sw[ws_name] = list(sw.get(ws_name, [])) + extra
    return base


def _source_key(source: dict) -> str:
    url = str(source.get("url") or "").strip()
    if url:
        try:
            parsed = urlparse(url)
        except Exception:
            parsed = None
        if parsed and parsed.netloc:
            netloc = parsed.netloc.lower().removeprefix("www.")
            path = parsed.path.rstrip("/") or "/"
            return f"{netloc}{path}".rstrip("/")
        return url.lower().rstrip("/")

    title = str(source.get("name") or source.get("title") or "").strip()
    return title.lower()


def _dedupe_sources(sources: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique_sources: list[dict] = []
    for source in sources:
        if not isinstance(source, dict):
            continue
        key = _source_key(source)
        if not key or key in seen:
            continue
        seen.add(key)
        unique_sources.append(source)
    return unique_sources


def _valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def manifest_sources(manifest: dict, workstream: str) -> list[dict]:
    try:
        ws = WORKSTREAM_ALIASES.get(workstream, workstream)
        workstreams = manifest.get("workstreams", {}) if isinstance(manifest, dict) else {}
        sources = workstreams.get(ws, []) if isinstance(workstreams, dict) else []
        if ws != workstream and isinstance(workstreams, dict):
            sources = _dedupe_sources(list(sources or []) + list(workstreams.get(workstream, []) or []))
        else:
            sources = _dedupe_sources(list(sources or []))
    except Exception:
        return []

    rows: list[dict] = []
    for source in sources:
        try:
            url = str(source.get("url") or "").strip()
            title = str(source.get("name") or source.get("title") or "").strip()
            if not url or not title or not _valid_url(url):
                continue
            rows.append(
                {
                    "source": "official",
                    "source_provider": "official_web",
                    "title": title,
                    "url": url,
                    "authority": source.get("authority", 1),
                    "source_institution": source.get("institution") or source.get("authority_name") or title,
                    "metadata_status": "official_manifest",
                    "query": workstream,
                    "provider_query": workstream,
                }
            )
        except Exception:
            continue
    return rows
