"""Language-independent concept-based retrieval helpers for OpenAlex.

OpenAlex "concepts" are language-agnostic: filtering ``works`` by a concept id
(e.g. ``concepts.id:C71924100``) returns matching documents in *all* languages,
not just the language of the search term used to discover the concept.

This module resolves free-text terms to short OpenAlex concept ids and caches
the mapping on disk so repeated runs avoid hitting the network. Every public
function is fail-soft: network/parse errors never raise, they degrade to
``None``/empty results so the surrounding pipeline keeps working offline.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

_CONCEPTS_FILENAME = "openalex_concepts.json"
_USER_AGENT = "NutEV Research Pipeline/1.0"


def _cache_path(config_root) -> Path:
    return Path(config_root) / _CONCEPTS_FILENAME


def load_concept_cache(config_root) -> dict[str, str]:
    """Load the term -> concept-id cache from ``<config_root>/openalex_concepts.json``.

    Returns an empty dict if the file is missing or invalid.
    """
    path = _cache_path(config_root)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    # Normalise to ``str -> str`` so downstream callers can rely on the shape.
    return {str(k): str(v) for k, v in raw.items()}


def save_concept_cache(config_root, cache: dict) -> None:
    """Persist the concept cache as sorted JSON. Best-effort: swallows errors."""
    path = _cache_path(config_root)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(cache, indent=2, ensure_ascii=False, sort_keys=True)
        path.write_text(payload, encoding="utf-8")
    except Exception as exc:  # pragma: no cover - defensive, best-effort write
        logger.debug("failed to save openalex concept cache path=%s error=%s", path, exc)


def resolve_concept_id(term, *, config_root, cache=None) -> str | None:
    """Resolve a single free-text ``term`` to a short OpenAlex concept id.

    Looks up a local cache first; an empty-string cache entry means
    "known-unresolved" and yields ``None`` without a network call. When the
    term is unknown and the network is enabled, queries the OpenAlex
    ``/concepts`` endpoint, caches the outcome (id or "" for no result), and
    returns the id or ``None``. Fail-soft on any error.
    """
    key = term.strip().lower()
    owns_cache = cache is None
    if cache is None:
        cache = load_concept_cache(config_root)

    if key in cache:
        # "" is a sentinel for "looked up before, no concept found".
        return cache[key] or None

    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        # No network allowed; only honour what is already cached.
        return cache.get(key) or None

    try:
        params: dict[str, object] = {"search": term, "per-page": 1}
        mailto = os.environ.get("OPENALEX_MAILTO")
        if mailto:
            params["mailto"] = mailto

        response = requests.get(
            "https://api.openalex.org/concepts",
            params=params,
            timeout=(10, 30),
            headers={"User-Agent": _USER_AGENT},
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results") or []

        concept_id = ""
        if results:
            raw_id = results[0].get("id") or ""
            # ``id`` is a URL like "https://openalex.org/C71924100"; keep the
            # trailing path segment (the short "C..." identifier).
            concept_id = str(raw_id).rstrip("/").rsplit("/", 1)[-1]

        cache[key] = concept_id
        # Only persist when we own the cache (single-term call). Batch callers
        # persist once after resolving everything.
        if owns_cache:
            save_concept_cache(config_root, cache)
        return concept_id or None

    except Exception as exc:
        logger.debug("openalex concept resolution failed term=%s error=%s", term, exc)
        return None


def resolve_concept_ids(terms, *, config_root) -> list[str]:
    """Resolve many terms to concept ids, deduped (order-preserving), no falsy."""
    cache = load_concept_cache(config_root)
    before = dict(cache)

    ids: list[str] = []
    seen: set[str] = set()
    for term in terms:
        concept_id = resolve_concept_id(term, config_root=config_root, cache=cache)
        if concept_id and concept_id not in seen:
            seen.add(concept_id)
            ids.append(concept_id)

    # Persist once if the shared cache picked up new entries.
    if cache != before:
        save_concept_cache(config_root, cache)

    return ids
