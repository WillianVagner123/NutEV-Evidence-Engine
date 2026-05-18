from __future__ import annotations

import csv
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request

PROMPT_VERSION = "nutev-llm-triage-v1"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_ENDPOINT = "https://api.openai.com/v1/chat/completions"
DEFAULT_MAX_RECORDS = 80
DEFAULT_BATCH_SIZE = 8


@dataclass(frozen=True)
class OpenAITriageConfig:
    enabled: bool
    api_key: str | None
    model: str = DEFAULT_MODEL
    endpoint: str = DEFAULT_ENDPOINT
    max_records: int = DEFAULT_MAX_RECORDS
    batch_size: int = DEFAULT_BATCH_SIZE
    timeout_seconds: int = 45
    max_retries: int = 2
    temperature: float = 0.0

    @classmethod
    def from_env(cls, enabled: bool) -> "OpenAITriageConfig":
        return cls(
            enabled=enabled,
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("NUTEV_OPENAI_MODEL")
            or os.getenv("OPENAI_MODEL")
            or DEFAULT_MODEL,
            endpoint=os.getenv("NUTEV_OPENAI_ENDPOINT") or DEFAULT_ENDPOINT,
            max_records=_env_int("NUTEV_LLM_MAX_RECORDS", DEFAULT_MAX_RECORDS),
            batch_size=max(1, _env_int("NUTEV_LLM_BATCH_SIZE", DEFAULT_BATCH_SIZE)),
            timeout_seconds=_env_int("NUTEV_LLM_TIMEOUT_SECONDS", 45),
            max_retries=max(0, _env_int("NUTEV_LLM_MAX_RETRIES", 2)),
            temperature=_env_float("NUTEV_LLM_TEMPERATURE", 0.0),
        )


SYSTEM_PROMPT = """You are a scientific evidence triage assistant for the NutMEV search method.

Your role is limited: prioritize and justify records for human screening. Do not make
final inclusion decisions and do not invent missing metadata.

Return JSON only in this schema:
{
  "items": [
    {
      "row_index": 0,
      "priority": "high|medium|low",
      "inclusion_vote": "include|maybe|exclude",
      "evidence_type": "guideline|systematic_review|trial|observational|framework|instrument|policy|other",
      "exclusion_reason": "",
      "rationale": "short audit-ready rationale",
      "confidence": 0.0
    }
  ]
}

Use high priority for records that clearly support NutMEV evidence mapping:
adult nutrition education, dietary patterns, food literacy, obesity, methods,
frameworks, instruments, guidelines, reviews, intervention trials, or implementation evidence.
Use low priority when metadata is off-topic, pediatric-only, animal-only, unrelated clinical scope,
or not useful for methodology/evidence synthesis.
"""


def triage_records(
    records: list[dict[str, Any]],
    workstream: str,
    logs_dir: Path,
    logger,
    *,
    enabled: bool,
    config: OpenAITriageConfig | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run an optional, auditable OpenAI triage layer over ranked metadata rows.

    The LLM never replaces the deterministic search, deduplication, or classic score.
    It only adds prioritization columns and writes JSONL/CSV audit artifacts.
    """

    cfg = config or OpenAITriageConfig.from_env(enabled)
    logs_dir.mkdir(parents=True, exist_ok=True)

    base_stats: dict[str, Any] = {
        "workstream": workstream,
        "enabled": cfg.enabled,
        "model": cfg.model,
        "prompt_version": PROMPT_VERSION,
        "candidate_records": len(records),
        "max_records": cfg.max_records,
        "completed": 0,
        "failed": 0,
        "status": "disabled",
    }

    if not cfg.enabled:
        _write_llm_summary(logs_dir, workstream, base_stats)
        return records, base_stats

    if not cfg.api_key:
        base_stats["status"] = "not_configured"
        _safe_log(
            logger,
            "warning",
            "LLM triage requested for ws=%s, but OPENAI_API_KEY is not configured",
            workstream,
        )
        _write_llm_summary(logs_dir, workstream, base_stats)
        return records, base_stats

    candidates = records[: max(0, cfg.max_records)]
    audit_entries: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []

    for batch in _batched(list(enumerate(candidates)), cfg.batch_size):
        try:
            items = _triage_batch(batch, workstream, cfg)
            by_index = {
                int(item.get("row_index")): _normalize_item(item)
                for item in items
                if str(item.get("row_index", "")).isdigit()
            }
        except Exception as exc:  # noqa: BLE001 - keep pipeline resilient
            base_stats["failed"] += len(batch)
            _safe_log(
                logger,
                "warning",
                "LLM triage failed ws=%s batch_start=%s error=%s",
                workstream,
                batch[0][0] if batch else "",
                exc,
            )
            for row_index, row in batch:
                entry = _audit_entry(row_index, row, workstream, cfg, status="error")
                entry["error"] = str(exc)
                audit_entries.append(entry)
            continue

        for row_index, row in batch:
            normalized = by_index.get(row_index)
            if normalized is None:
                base_stats["failed"] += 1
                entry = _audit_entry(row_index, row, workstream, cfg, status="missing")
                audit_entries.append(entry)
                continue

            _apply_triage(row, normalized, cfg)
            base_stats["completed"] += 1
            entry = _audit_entry(row_index, row, workstream, cfg, status="completed")
            entry.update(normalized)
            audit_entries.append(entry)
            summary_rows.append(
                {
                    "workstream": workstream,
                    "row_index": row_index,
                    "title": str(row.get("title") or "")[:500],
                    "doi": row.get("doi", ""),
                    "pmid": row.get("pmid", ""),
                    "source": row.get("source", ""),
                    "relevance_score": row.get("relevance_score", ""),
                    "llm_priority": normalized["priority"],
                    "llm_inclusion_vote": normalized["inclusion_vote"],
                    "llm_evidence_type": normalized["evidence_type"],
                    "llm_confidence": normalized["confidence"],
                    "llm_exclusion_reason": normalized["exclusion_reason"],
                    "llm_rationale": normalized["rationale"],
                    "llm_model": cfg.model,
                    "llm_prompt_version": PROMPT_VERSION,
                }
            )

    _append_jsonl(logs_dir / "llm_triage.jsonl", audit_entries)
    _write_llm_csv(logs_dir / f"llm_triage_{workstream}.csv", summary_rows)
    base_stats["status"] = "completed" if base_stats["completed"] else "no_completed_items"
    _write_llm_summary(logs_dir, workstream, base_stats)
    return records, base_stats


def rerank_records_by_llm(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Use LLM priority as a secondary audit layer without discarding records."""

    priority_rank = {"high": 3, "medium": 2, "low": 1}
    vote_rank = {"include": 3, "maybe": 2, "exclude": 1}

    def sort_key(row: dict[str, Any]) -> tuple[int, int, float]:
        return (
            priority_rank.get(str(row.get("llm_priority") or "").lower(), 0),
            vote_rank.get(str(row.get("llm_inclusion_vote") or "").lower(), 0),
            float(row.get("relevance_score") or 0),
        )

    return sorted(records, key=sort_key, reverse=True)


def _triage_batch(
    batch: list[tuple[int, dict[str, Any]]],
    workstream: str,
    cfg: OpenAITriageConfig,
) -> list[dict[str, Any]]:
    payload = {
        "workstream": workstream,
        "prompt_version": PROMPT_VERSION,
        "items": [
            {
                "row_index": row_index,
                "metadata": _record_payload(row),
            }
            for row_index, row in batch
        ],
    }
    response = _chat_completion(
        cfg,
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=False),
            },
        ],
    )
    content = _extract_message_content(response)
    parsed = _parse_json_object(content)
    items = parsed.get("items", [])
    if not isinstance(items, list):
        raise ValueError("LLM response did not include an items list")
    return [item for item in items if isinstance(item, dict)]


def _chat_completion(
    cfg: OpenAITriageConfig,
    messages: list[dict[str, str]],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": cfg.model,
        "messages": messages,
        "temperature": cfg.temperature,
        "response_format": {"type": "json_object"},
    }

    last_exc: Exception | None = None
    for attempt in range(cfg.max_retries + 1):
        try:
            return _post_json(cfg, payload)
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            last_exc = RuntimeError(f"OpenAI HTTP {exc.code}: {body[:700]}")
            if exc.code == 400 and "response_format" in body:
                payload.pop("response_format", None)
            if attempt >= cfg.max_retries:
                raise last_exc
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt >= cfg.max_retries:
                raise
        time.sleep(min(2**attempt, 8))
    if last_exc:
        raise last_exc
    raise RuntimeError("OpenAI call failed without exception")


def _post_json(cfg: OpenAITriageConfig, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        cfg.endpoint,
        data=data,
        headers={
            "Authorization": f"Bearer {cfg.api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=cfg.timeout_seconds) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def _extract_message_content(response: dict[str, Any]) -> str:
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Unexpected OpenAI response shape") from exc
    if not isinstance(content, str):
        raise ValueError("OpenAI message content is not a string")
    return content


def _parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.DOTALL | re.I)
    if fence:
        cleaned = fence.group(1).strip()
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("LLM response is not a JSON object")
    return parsed


def _record_payload(row: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "title",
        "abstract",
        "summary",
        "journal",
        "year",
        "source",
        "doi",
        "pmid",
        "pmcid",
        "url",
        "document_type",
        "publication_type",
        "relevance_score",
        "workstream",
    ]
    payload: dict[str, Any] = {}
    for field in fields:
        value = row.get(field)
        if value in (None, "", [], {}):
            continue
        payload[field] = _truncate(
            value,
            limit=1600 if field in {"abstract", "summary"} else 500,
        )
    return payload


def _normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    priority = _choice(item.get("priority"), {"high", "medium", "low"}, "medium")
    vote = _choice(item.get("inclusion_vote"), {"include", "maybe", "exclude"}, "maybe")
    evidence_type = _choice(
        item.get("evidence_type"),
        {
            "guideline",
            "systematic_review",
            "trial",
            "observational",
            "framework",
            "instrument",
            "policy",
            "other",
        },
        "other",
    )
    return {
        "priority": priority,
        "inclusion_vote": vote,
        "evidence_type": evidence_type,
        "exclusion_reason": str(item.get("exclusion_reason") or "")[:300],
        "rationale": str(item.get("rationale") or "")[:500],
        "confidence": _confidence(item.get("confidence")),
    }


def _apply_triage(row: dict[str, Any], item: dict[str, Any], cfg: OpenAITriageConfig) -> None:
    row["llm_triage_status"] = "completed"
    row["llm_priority"] = item["priority"]
    row["llm_inclusion_vote"] = item["inclusion_vote"]
    row["llm_evidence_type"] = item["evidence_type"]
    row["llm_exclusion_reason"] = item["exclusion_reason"]
    row["llm_rationale"] = item["rationale"]
    row["llm_confidence"] = item["confidence"]
    row["llm_model"] = cfg.model
    row["llm_prompt_version"] = PROMPT_VERSION


def _audit_entry(
    row_index: int,
    row: dict[str, Any],
    workstream: str,
    cfg: OpenAITriageConfig,
    *,
    status: str,
) -> dict[str, Any]:
    return {
        "workstream": workstream,
        "row_index": row_index,
        "status": status,
        "title": str(row.get("title") or "")[:500],
        "doi": row.get("doi", ""),
        "pmid": row.get("pmid", ""),
        "source": row.get("source", ""),
        "url": row.get("url", ""),
        "relevance_score": row.get("relevance_score", ""),
        "model": cfg.model,
        "prompt_version": PROMPT_VERSION,
    }


def _append_jsonl(path: Path, entries: list[dict[str, Any]]) -> None:
    if not entries:
        return
    with path.open("a", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")


def _write_llm_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_llm_summary(logs_dir: Path, workstream: str, stats: dict[str, Any]) -> None:
    (logs_dir / f"llm_triage_summary_{workstream}.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _batched(
    items: list[tuple[int, dict[str, Any]]],
    size: int,
) -> list[list[tuple[int, dict[str, Any]]]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _choice(value: Any, allowed: set[str], default: str) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in allowed else default


def _confidence(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _truncate(value: Any, *, limit: int) -> Any:
    if isinstance(value, str):
        return value[:limit]
    return value


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _safe_log(logger, level: str, message: str, *args: Any) -> None:
    if logger is None:
        return
    log_fn = getattr(logger, level, None)
    if callable(log_fn):
        log_fn(message, *args)
