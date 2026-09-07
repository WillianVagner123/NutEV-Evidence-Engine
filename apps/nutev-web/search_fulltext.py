from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import threading
from typing import Any, Callable
from uuid import uuid4

from nutev.registry.full_text import record_full_text_artifact
from nutev.science.enrichment import (
    _content_signals,
    _download,
    _extract_local_file,
    _section_blocks,
)
from nutev.science.full_text_probe import select_reachable_candidate
from nutev.science.full_text_resolver import resolve_full_text_candidates


MAX_AUTO_FULL_TEXT = 10
_CACHE_ROOT_NAME = "16_search_full_text_cache"
_CACHE_LOCKS: dict[str, threading.Lock] = {}
_CACHE_LOCKS_GUARD = threading.Lock()
ProgressCallback = Callable[[dict[str, Any]], None]


def configured_full_text_limit() -> int:
    """Return the bounded automatic enrichment budget for public web searches.

    The default is deliberately zero outside configured deployments so library and
    unit-test callers do not unexpectedly start network retrieval. Production can
    opt in with ``NUTEV_SEARCH_FULLTEXT_LIMIT``.
    """

    raw = str(os.environ.get("NUTEV_SEARCH_FULLTEXT_LIMIT", "0") or "0").strip()
    try:
        value = int(raw)
    except ValueError:
        return 0
    return max(0, min(value, MAX_AUTO_FULL_TEXT))


def _emit(callback: ProgressCallback | None, event: dict[str, Any]) -> None:
    if callback is None:
        return
    try:
        callback(event)
    except Exception:
        return


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().casefold() in {
        "1",
        "true",
        "yes",
        "y",
        "open",
        "open access",
        "oa",
        "free",
    }


def _recorded_full_text_hint(row: dict[str, Any]) -> bool:
    if str(row.get("pmcid") or row.get("pmc_id") or "").strip():
        return True
    if any(
        str(row.get(field) or "").strip()
        for field in ("pdf_url", "full_text_url", "open_access_url", "oa_url")
    ):
        return True
    return _truthy(row.get("is_open_access"))


def _identity_seed(row: dict[str, Any]) -> str:
    # Once search persistence has assigned a durable NutEV identity, every provider
    # and every future search must converge on the same full-text cache directory.
    article_id = str(row.get("article_id") or "").strip()
    if article_id:
        return f"article_id:{article_id}"
    for field in (
        "pmcid",
        "pmc_id",
        "pmid",
        "doi",
        "openalex_id",
        "url",
        "title",
    ):
        value = str(row.get(field) or "").strip().casefold()
        if value:
            return f"{field}:{value}"
    return json.dumps(row, ensure_ascii=False, sort_keys=True, default=str)


def _cache_key(row: dict[str, Any]) -> str:
    return sha256(_identity_seed(row).encode("utf-8")).hexdigest()[:32]


def _cache_lock(key: str) -> threading.Lock:
    with _CACHE_LOCKS_GUARD:
        return _CACHE_LOCKS.setdefault(key, threading.Lock())


def _atomic_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(path)


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    _atomic_text(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
    )


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _public_manifest(value: dict[str, Any], *, cache_hit: bool) -> dict[str, Any]:
    allowed = (
        "status",
        "scope",
        "selected_url",
        "resolver_route",
        "resolver_source",
        "media_type",
        "extraction_method",
        "ocr_used",
        "ocr_engine",
        "text_chars",
        "section_count",
        "section_headings",
        "design_signals",
        "warnings",
        "probe_attempts",
        "candidate_count",
        "article_id",
        "artifact_id",
        "content_sha256",
        "text_sha256",
        "registry_linked",
    )
    output = {key: value.get(key) for key in allowed if key in value}
    output.update(
        {
            "cache_hit": cache_hit,
            "processing_policy": "selective_top_ranked_open_full_text",
            "ranking_influence": "none",
        }
    )
    return output


def _link_manifest_to_registry(
    manifest: dict[str, Any],
    *,
    row: dict[str, Any],
    output_root: Path,
    cache_dir: Path,
) -> dict[str, Any]:
    article_id = str(row.get("article_id") or manifest.get("article_id") or "").strip()
    if not article_id:
        manifest["registry_linked"] = False
        return manifest
    linked = record_full_text_artifact(
        output_root=output_root,
        article_id=article_id,
        manifest=manifest,
        cache_dir=cache_dir,
    )
    manifest["article_id"] = article_id
    if linked.get("status") == "linked":
        manifest["artifact_id"] = linked.get("artifact_id")
        manifest["registry_linked"] = True
    else:
        manifest["registry_linked"] = False
        manifest["registry_link_error"] = linked.get("reason")
    return manifest


def _load_cached(
    cache_dir: Path,
    *,
    row: dict[str, Any],
    output_root: Path,
) -> dict[str, Any] | None:
    manifest_path = cache_dir / "manifest.json"
    text_path = cache_dir / "private-text.txt"
    if not manifest_path.is_file() or not text_path.is_file():
        return None
    try:
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict) or value.get("status") != "extracted":
        return None
    expected = str(value.get("private_text_sha256") or value.get("text_sha256") or "").strip().lower()
    if not expected:
        return None
    try:
        actual = sha256(text_path.read_bytes()).hexdigest()
    except OSError:
        return None
    if actual != expected:
        return None
    # Caches created after Article Registry activation are self-healing: if the
    # SQLite projection was rebuilt, the cached manifest can recreate the artifact
    # link without downloading or OCRing the document again.
    if value.get("content_sha256"):
        value = _link_manifest_to_registry(
            value,
            row=row,
            output_root=output_root,
            cache_dir=cache_dir,
        )
        _atomic_json(manifest_path, value)
    return _public_manifest(value, cache_hit=True)


def _full_text_candidates(row: dict[str, Any], *, allow_network: bool) -> list[dict[str, Any]]:
    # Prefer already-recorded identifiers/URLs first. Only consult network
    # resolvers when those do not provide a demonstrable full-text candidate.
    recorded = resolve_full_text_candidates(
        row,
        include_network_resolvers=False,
    )
    recorded_full = [item for item in recorded if item.get("scope") == "full_text"]
    if recorded_full or not allow_network:
        return recorded_full
    expanded = resolve_full_text_candidates(
        row,
        include_network_resolvers=True,
    )
    return [item for item in expanded if item.get("scope") == "full_text"]


def _effective_media_type(candidate: dict[str, Any], downloaded_type: str) -> str | None:
    expected = str(candidate.get("media_type") or "").strip() or None
    actual = str(downloaded_type or "").strip().casefold()
    if expected and actual in {"", "application/octet-stream", "binary/octet-stream"}:
        return expected
    return downloaded_type or expected


def _extract_candidate(
    candidate: dict[str, Any],
    *,
    row: dict[str, Any],
    output_root: Path,
    cache_dir: Path,
    key: str,
    candidate_count: int,
    probe_attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    downloaded_path, downloaded_type, final_url = _download(
        str(candidate.get("url") or ""),
        cache_dir / "private-assets",
    )
    media_type = _effective_media_type(candidate, downloaded_type)
    content_sha = _file_sha256(downloaded_path)
    text, method, ocr_used, ocr_engine, warnings = _extract_local_file(
        downloaded_path,
        media_type,
    )
    if not text.strip():
        raise RuntimeError("full_text_extraction_produced_no_text")

    blocks = _section_blocks(text, f"search-full-text:{key}")
    signals = _content_signals(text, blocks)
    private_text_path = cache_dir / "private-text.txt"
    _atomic_text(private_text_path, text)
    private_sha = sha256(text.encode("utf-8")).hexdigest()
    method_value = getattr(method, "value", str(method))
    manifest = {
        "schema_version": 2,
        "status": "extracted",
        "scope": "full_text",
        "article_id": str(row.get("article_id") or "").strip() or None,
        "selected_url": final_url,
        "resolver_route": candidate.get("resolver_route"),
        "resolver_source": candidate.get("resolver_source"),
        "media_type": media_type,
        "content_sha256": content_sha,
        "text_sha256": private_sha,
        "extraction_method": method_value,
        "ocr_used": bool(ocr_used),
        "ocr_engine": ocr_engine,
        "text_chars": len(text),
        "section_count": len(blocks),
        "section_headings": [str(block.heading or "") for block in blocks[:12]],
        "design_signals": list(signals.get("study_design_signals") or [])[:12],
        "warnings": list(warnings or [])[:20],
        "probe_attempts": len(probe_attempts),
        "candidate_count": candidate_count,
        "private_text_file": private_text_path.name,
        "private_text_sha256": private_sha,
        "cache_key": key,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "ranking_influence": "none",
    }
    manifest = _link_manifest_to_registry(
        manifest,
        row=row,
        output_root=output_root,
        cache_dir=cache_dir,
    )
    _atomic_json(cache_dir / "manifest.json", manifest)
    return _public_manifest(manifest, cache_hit=False)


def _enrich_one(
    row: dict[str, Any],
    *,
    output_root: Path,
    allow_network: bool,
) -> dict[str, Any]:
    key = _cache_key(row)
    cache_dir = output_root / _CACHE_ROOT_NAME / key
    with _cache_lock(key):
        cached = _load_cached(
            cache_dir,
            row=row,
            output_root=output_root,
        )
        if cached is not None:
            return cached

        candidates = _full_text_candidates(row, allow_network=allow_network)
        if not candidates:
            return {
                "status": "not_found",
                "candidate_count": 0,
                "cache_hit": False,
                "processing_policy": "selective_top_ranked_open_full_text",
                "ranking_influence": "none",
            }
        if not allow_network:
            return {
                "status": "candidate_available_not_processed",
                "candidate_count": len(candidates),
                "cache_hit": False,
                "processing_policy": "selective_top_ranked_open_full_text",
                "ranking_influence": "none",
            }

        selected, attempts = select_reachable_candidate(
            candidates,
            allow_network=True,
            max_candidates=min(10, len(candidates)),
        )
        if not selected or selected.get("probe_selected") is not True:
            return {
                "status": "unreachable",
                "candidate_count": len(candidates),
                "probe_attempts": len(attempts),
                "cache_hit": False,
                "processing_policy": "selective_top_ranked_open_full_text",
                "ranking_influence": "none",
            }
        return _extract_candidate(
            selected,
            row=row,
            output_root=output_root,
            cache_dir=cache_dir,
            key=key,
            candidate_count=len(candidates),
            probe_attempts=attempts,
        )


def enrich_ranked_results(
    rows: list[dict[str, Any]],
    *,
    output_root: Path,
    search_id: str,
    limit: int,
    allow_network: bool,
    on_progress: ProgressCallback | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Selectively attach full-text/OCR provenance without changing ranking.

    Only the top ``limit`` ranked records are eligible for automatic retrieval.
    Extracted text stays in a server-side cache and is intentionally omitted from
    the public result JSON. The article's existing score/rank are never changed.
    """

    bounded = max(0, min(int(limit), MAX_AUTO_FULL_TEXT, len(rows)))
    summary: dict[str, Any] = {
        "enabled": bool(bounded and allow_network),
        "status": "disabled" if not bounded else ("network_disabled" if not allow_network else "running"),
        "policy": "selective_top_ranked_open_full_text",
        "budget": bounded,
        "selected": bounded,
        "attempted": 0,
        "extracted": 0,
        "ocr_used": 0,
        "cache_hits": 0,
        "not_found": 0,
        "unreachable": 0,
        "failed": 0,
        "candidate_available_not_processed": 0,
        "ranking_unchanged": True,
        "public_payload_contains_full_text": False,
        "search_id": search_id,
    }

    for index, original in enumerate(rows):
        row = original
        if index >= bounded:
            status = "candidate_available_not_processed" if _recorded_full_text_hint(row) else "not_checked"
            row["full_text"] = {
                "status": status,
                "processing_policy": "selective_top_ranked_open_full_text",
                "ranking_influence": "none",
            }
            if status == "candidate_available_not_processed":
                summary["candidate_available_not_processed"] += 1
            continue

        _emit(
            on_progress,
            {
                "type": "full_text_item_started",
                "search_id": search_id,
                "index": index + 1,
                "total": bounded,
                "reference_rank": row.get("reference_rank"),
            },
        )
        before_rank = row.get("reference_rank")
        before_score = row.get("reference_score")
        summary["attempted"] += 1
        try:
            enrichment = _enrich_one(
                row,
                output_root=output_root,
                allow_network=allow_network,
            )
        except Exception as exc:
            enrichment = {
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "processing_policy": "selective_top_ranked_open_full_text",
                "ranking_influence": "none",
            }
        row["full_text"] = enrichment

        # Defensive invariant: full-text availability cannot change a rank when
        # only a selected prefix was enriched.
        row["reference_rank"] = before_rank
        row["reference_score"] = before_score

        status = str(enrichment.get("status") or "failed")
        if status == "extracted":
            summary["extracted"] += 1
            if enrichment.get("ocr_used"):
                summary["ocr_used"] += 1
            if enrichment.get("cache_hit"):
                summary["cache_hits"] += 1
        elif status in {"not_found", "unreachable", "failed"}:
            summary[status] += 1
        elif status == "candidate_available_not_processed":
            summary["candidate_available_not_processed"] += 1

        _emit(
            on_progress,
            {
                "type": "full_text_item_completed",
                "search_id": search_id,
                "index": index + 1,
                "total": bounded,
                "reference_rank": row.get("reference_rank"),
                "status": status,
                "ocr_used": bool(enrichment.get("ocr_used")),
            },
        )

    if bounded and allow_network:
        summary["status"] = "completed_with_gaps" if summary["failed"] or summary["unreachable"] else "completed"
    _emit(on_progress, {"type": "full_text_completed", **summary})
    return rows, summary
