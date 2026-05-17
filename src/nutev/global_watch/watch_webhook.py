from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

from nutev.engine.events import emit_event, write_event


def _why(item: dict) -> str:
    text = (
        f"{item.get('title', '')} "
        f"{item.get('evidence_type', '')} "
        f"{item.get('category', '')}"
    ).lower()
    if "guideline" in text:
        return "Pode alterar recomendações ou base metodológica do protocolo NutMEV."
    if "systematic review" in text or "meta-analysis" in text:
        return "Pode consolidar evidência para síntese e discussão."
    if "trial" in text:
        return "Pode informar intervenções e desfechos práticos."
    if any(
        key in text for key in ["framework", "questionnaire", "instrument"]
    ):
        return "Pode apoiar o desenvolvimento do Artigo 3 e instrumento NutMEV."
    if any(
        key in text for key in ["adherence", "implementation", "feasibility"]
    ):
        return "Pode apoiar adesão, viabilidade e implementação."
    return "Pode contribuir para monitoramento científico contínuo do NutMEV."


def build_webhook_payload(
    rows: list[dict],
    digest_path: Path,
    run_summary: dict,
    max_items: int = 10,
) -> dict:
    top = rows[:max_items]
    summary = {
        "total_items": run_summary.get("total_items", len(rows)),
        "new_items": run_summary.get("new_items", 0),
        "high_priority": run_summary.get("high_priority", 0),
        "pdf": run_summary.get("pdf", 0),
        "html_snapshot": run_summary.get("html_snapshot", 0),
        "metadata_only": run_summary.get("metadata_only", 0),
        "failed": run_summary.get("failed", 0),
    }
    payload = {
        "project": "NutMEV Global Watch",
        "run_date": datetime.now(timezone.utc).date().isoformat(),
        "mode": run_summary.get("mode", "unknown"),
        "summary": summary,
        "digest_path": str(digest_path),
        "top_items": [
            {
                "priority": index + 1,
                "title": row.get("title"),
                "evidence_type": row.get("evidence_type"),
                "source_provider": row.get("source_provider"),
                "category": row.get("category"),
                "workstream_affinity": row.get("workstream_affinity", []),
                "url": row.get("url"),
                "doi": row.get("doi"),
                "download_status": row.get("download_status", "metadata_only"),
                "watch_score": row.get("watch_score", 0),
                "why_it_matters": row.get("why_it_matters") or _why(row),
            }
            for index, row in enumerate(top)
        ],
    }
    top_title = top[0].get("title") if top else "n/a"
    payload["text"] = (
        f"NutMEV Global Watch: {summary['new_items']} novos achados. "
        f"Top: {top_title}"
    )
    return payload


def send_webhook(
    payload: dict,
    webhook_url: str,
    logger,
    run_id: str,
    logs_dir: Path,
) -> dict:
    host = urlparse(webhook_url).netloc or "configured"
    write_event(
        emit_event(
            run_id,
            "webhook_started",
            "Webhook started",
            meta_json={"host": host},
        ),
        logs_dir / "run_events.jsonl",
    )
    last_error = "http_error"
    for attempt in range(1, 3):
        try:
            response = requests.post(webhook_url, json=payload, timeout=20)
            if response.status_code < 400:
                write_event(
                    emit_event(
                        run_id,
                        "webhook_sent",
                        "Webhook sent",
                        meta_json={"host": host, "status": response.status_code},
                    ),
                    logs_dir / "run_events.jsonl",
                )
                return {"status": "sent", "http_status": response.status_code}
            last_error = f"http_{response.status_code}"
        except Exception as exc:
            last_error = str(exc)
            logger.warning("webhook attempt=%s host=%s failed", attempt, host)
    write_event(
        emit_event(
            run_id,
            "webhook_failed",
            "Webhook failed",
            event_kind="warning",
            meta_json={"host": host, "error": last_error},
        ),
        logs_dir / "run_events.jsonl",
    )
    return {"status": "failed"}


def maybe_send_webhook(
    rows: list[dict],
    digest_path: Path,
    run_summary: dict,
    settings,
    logger,
    run_id: str,
    enabled: bool,
    webhook_url: str | None = None,
) -> dict:
    logs_dir = settings.output_dirs["07_logs"]
    enabled = enabled or os.getenv("NUTEV_NOTIFY_WEBHOOK") == "1"
    if not enabled:
        write_event(
            emit_event(run_id, "webhook_skipped", "Webhook disabled"),
            logs_dir / "run_events.jsonl",
        )
        return {"status": "skipped", "reason": "disabled"}

    url = webhook_url or os.getenv("NUTEV_DIGEST_WEBHOOK_URL")
    if not url:
        write_event(
            emit_event(run_id, "webhook_skipped", "Webhook URL not configured"),
            logs_dir / "run_events.jsonl",
        )
        return {"status": "skipped", "reason": "missing_url"}

    payload = build_webhook_payload(rows, digest_path, run_summary)
    run_dir = digest_path.parent
    (run_dir / "webhook_payload.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return send_webhook(payload, url, logger, run_id, logs_dir)
