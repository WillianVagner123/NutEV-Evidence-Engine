from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

from nutev.download.resolver import resolve_url
from nutev.engine.events import emit_event, write_event
from nutev.global_watch.watch_html_extract import extract_clean_html_text

MODE_CAPTURE_LIMITS = {"quick": 10, "thesis": 30, "exhaustive": 100}


def resolve_watch_item_url(item: dict) -> dict:
    original = (
        item.get("final_url")
        or item.get("url")
        or (f"https://doi.org/{item.get('doi')}" if item.get("doi") else "")
    )
    if not original:
        item["failure_reason"] = "missing_url"
        return item

    final_url, _ = resolve_url(original)
    item["original_url"] = original
    item["final_url"] = final_url or original
    return item


def save_capture_json(item: dict, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    item.setdefault("artifact_paths", {})

    document_id = item.get("document_id") or "unknown_document"
    json_path = out_dir / f"{document_id}.json"

    payload = {
        "document_id": item.get("document_id"),
        "title": item.get("title"),
        "doi": item.get("doi"),
        "original_url": item.get("original_url"),
        "final_url": item.get("final_url"),
        "source_provider": item.get("source_provider"),
        "category": item.get("category"),
        "evidence_type": item.get("evidence_type"),
        "workstream_affinity": item.get("workstream_affinity"),
        "download_status": item.get("download_status"),
        "capture_status": item.get("capture_status"),
        "artifact_paths": item.get("artifact_paths"),
        "failure_reason": item.get("failure_reason"),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "host": item.get("host"),
        "content_type": item.get("content_type"),
        "http_status": item.get("http_status"),
        "abstract": item.get("abstract"),
        "headings": item.get("headings", []),
        "doi_candidates": item.get("doi_candidates", []),
        "pdf_links_found": item.get("pdf_links_found", []),
    }

    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    item["artifact_paths"]["json"] = str(json_path)
    return item


def save_metadata_only(item: dict, reason: str, out_dir: Path) -> dict:
    item["download_status"] = "metadata_only"
    item["capture_status"] = "metadata_only"
    item["failure_reason"] = reason
    return save_capture_json(item, out_dir)


def _event_path(settings) -> Path:
    return settings.output_dirs["07_logs"] / "run_events.jsonl"


def _emit(settings, run_id: str, event_name: str, message: str, item: dict, **kwargs) -> None:
    write_event(
        emit_event(
            run_id,
            event_name,
            message,
            document_id=item.get("document_id"),
            **kwargs,
        ),
        _event_path(settings),
    )


def _is_synthetic_fallback(item: dict) -> bool:
    candidate_urls = [
        str(item.get("url") or ""),
        str(item.get("final_url") or ""),
        str(item.get("original_url") or ""),
    ]
    return item.get("source_provider") == "watch_seed" or any(
        "fallback.local" in url for url in candidate_urls
    )


def capture_single_watch_item(item: dict, settings, logger, run_id: str) -> dict:
    captures_dir = settings.project_root / "09_global_watch" / "captures"
    captures_dir.mkdir(parents=True, exist_ok=True)

    _emit(settings, run_id, "capture_item_started", "Capture item started", item)

    try:
        if _is_synthetic_fallback(item):
            out = save_metadata_only(item, "synthetic_fallback_no_capture", captures_dir)
            _emit(settings, run_id, "metadata_only_saved", "Metadata only saved", item)
            return out

        if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
            out = save_metadata_only(item, "network_disabled", captures_dir)
            _emit(settings, run_id, "metadata_only_saved", "Metadata only saved", item)
            return out

        item = resolve_watch_item_url(item)

        if _is_synthetic_fallback(item):
            out = save_metadata_only(item, "synthetic_fallback_no_capture", captures_dir)
            _emit(settings, run_id, "metadata_only_saved", "Metadata only saved", item)
            return out

        final_url = item.get("final_url")

        if not final_url:
            out = save_metadata_only(item, "missing_url", captures_dir)
            _emit(settings, run_id, "metadata_only_saved", "Metadata only saved", item)
            return out

        item["host"] = urlparse(final_url).netloc.lower()
        item.setdefault("artifact_paths", {})

        r = requests.get(final_url, timeout=20, allow_redirects=True)
        item["http_status"] = r.status_code
        item["content_type"] = (r.headers.get("Content-Type") or "").lower()

        if r.status_code >= 400:
            out = save_metadata_only(item, f"http_{r.status_code}", captures_dir)
            _emit(settings, run_id, "metadata_only_saved", "Metadata only saved", item)
            return out

        if not r.content:
            out = save_metadata_only(item, "empty_content", captures_dir)
            _emit(settings, run_id, "metadata_only_saved", "Metadata only saved", item)
            return out

        if "pdf" in item["content_type"] or final_url.lower().endswith(".pdf"):
            if r.content[:5] != b"%PDF-":
                out = save_metadata_only(item, "invalid_pdf_header", captures_dir)
                _emit(settings, run_id, "metadata_only_saved", "Metadata only saved", item)
                return out

            pdf_path = captures_dir / f"{item['document_id']}.pdf"
            pdf_path.write_bytes(r.content)

            item["artifact_paths"]["pdf"] = str(pdf_path)
            item["download_status"] = "pdf"
            item["capture_status"] = "pdf"

            out = save_capture_json(item, captures_dir)
            _emit(settings, run_id, "capture_item_completed", "Capture item completed", item)
            return out

        html_path = captures_dir / f"{item['document_id']}.html"
        txt_path = captures_dir / f"{item['document_id']}.txt"

        html_path.write_bytes(r.content)

        extracted = extract_clean_html_text(r.text)
        txt_path.write_text(
            extracted.get("clean_text", ""),
            encoding="utf-8",
            errors="ignore",
        )

        item["title"] = item.get("title") or extracted.get("title")
        item["abstract"] = extracted.get("abstract")
        item["headings"] = extracted.get("headings", [])
        item["doi_candidates"] = extracted.get("doi_candidates", [])
        item["pdf_links_found"] = extracted.get("pdf_links_found", [])
        item["artifact_paths"]["html"] = str(html_path)
        item["artifact_paths"]["txt"] = str(txt_path)
        item["download_status"] = "html_snapshot"
        item["capture_status"] = "html_snapshot"

        out = save_capture_json(item, captures_dir)
        _emit(settings, run_id, "capture_item_completed", "Capture item completed", item)
        return out

    except Exception as exc:
        logger.warning("capture_item_failed doc=%s error=%s", item.get("document_id"), exc)

        write_event(
            emit_event(
                run_id,
                "capture_item_failed",
                "Capture item failed",
                event_kind="warning",
                document_id=item.get("document_id"),
                meta_json={"error": str(exc)},
            ),
            _event_path(settings),
        )

        out = save_metadata_only(item, str(exc), captures_dir)
        _emit(settings, run_id, "metadata_only_saved", "Metadata only saved", item)
        return out


def capture_watch_items(
    items: list[dict],
    settings,
    logger,
    run_id: str,
    mode: str,
    capture_limit: int | None = None,
) -> tuple[list[dict], list[dict]]:
    write_event(
        emit_event(run_id, "capture_started", "Capture started"),
        _event_path(settings),
    )

    limit = capture_limit if capture_limit is not None else MODE_CAPTURE_LIMITS.get(mode, 30)
    selected = items[:limit]

    captured = [
        capture_single_watch_item(dict(item), settings, logger, run_id)
        for item in selected
    ]

    by_id = {row.get("document_id"): row for row in captured}
    merged = [by_id.get(item.get("document_id"), item) for item in items]

    write_event(
        emit_event(
            run_id,
            "capture_completed",
            "Capture completed",
            meta_json={"captured": len(captured)},
        ),
        _event_path(settings),
    )

    return merged, captured
