from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

import requests

from nutev.audit_guardrails import sha256_file
from nutev.reference_identity import canonical_identity


SCHEMA_VERSION = "nutev.jev-semantic-shadow.v1"
DEFAULT_BASE_URL = "https://api.typesafe.ai"
DEFAULT_MODEL = "jev-latest"
DEFAULT_TIMEOUT_SECONDS = 3.0
DEFAULT_LIMIT = 20

DOCUMENT_TYPES = {
    "randomized_trial": "Randomized or quasi-randomized intervention trial.",
    "cohort": "Prospective or retrospective cohort study.",
    "cross_sectional": "Cross-sectional observational study.",
    "case_control": "Case-control study.",
    "systematic_review": "Systematic review, with or without meta-analysis.",
    "meta_analysis": "Meta-analysis presented as the primary document type.",
    "guideline": "Clinical practice guideline, consensus, standard, or formal recommendation document.",
    "narrative_review": "Narrative, scoping, integrative, or other non-systematic review.",
    "commentary": "Editorial, commentary, viewpoint, letter, or opinion piece.",
    "other": "None of the other document-type labels can be supported from the supplied metadata.",
}


@dataclass(frozen=True)
class JevConfig:
    mode: str
    api_key: str
    base_url: str
    model: str
    timeout_seconds: float
    limit: int


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _safe_mode(value: str | None) -> str:
    normalized = (value or "off").strip().lower()
    return normalized if normalized in {"off", "shadow"} else "off"


def _bounded_timeout(value: str | float | int | None) -> float:
    try:
        parsed = float(value if value is not None else DEFAULT_TIMEOUT_SECONDS)
    except (TypeError, ValueError):
        parsed = DEFAULT_TIMEOUT_SECONDS
    return max(0.5, min(15.0, parsed))


def _bounded_limit(value: str | int | None) -> int:
    try:
        parsed = int(value if value is not None else DEFAULT_LIMIT)
    except (TypeError, ValueError):
        parsed = DEFAULT_LIMIT
    return max(1, min(500, parsed))


def load_config(*, mode: str | None = None, limit: int | None = None) -> JevConfig:
    return JevConfig(
        mode=_safe_mode(mode if mode is not None else os.getenv("NUTEV_JEV_MODE")),
        api_key=os.getenv("TYPESAFE_API_KEY", "").strip(),
        base_url=os.getenv("TYPESAFE_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        model=os.getenv("TYPESAFE_DEFAULT_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL,
        timeout_seconds=_bounded_timeout(os.getenv("NUTEV_JEV_TIMEOUT_SECONDS")),
        limit=_bounded_limit(limit if limit is not None else os.getenv("NUTEV_JEV_MAX_RECORDS")),
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise RuntimeError(f"Non-object JSONL at {path}:{line_number}")
            rows.append(value)
    return rows


def _atomic_text(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    return sha256_file(path)


def _write_json(path: Path, value: Any) -> str:
    return _atomic_text(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
    )


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> str:
    return _atomic_text(
        path,
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, default=str) + "\n"
            for row in rows
        ),
    )


def _clip(value: Any, maximum: int) -> str:
    text = str(value or "").strip()
    return text[:maximum]


def semantic_state(row: dict[str, Any]) -> dict[str, Any]:
    """
    Metadata-only state for the external semantic judge.

    The shadow layer never sends full text/PDFs, review decisions, project bindings,
    machine ranking/tier, human eligibility/PRISMA state, or private workspace metadata.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "title": _clip(row.get("title"), 600),
        "abstract_or_snippet": _clip(
            row.get("abstract") or row.get("summary") or row.get("snippet"),
            4000,
        ),
        "keywords": _clip(
            row.get("keywords") or row.get("keyword") or row.get("subjects"),
            1200,
        ),
        "article_type": _clip(row.get("article_type"), 300),
        "publication_year": row.get("reference_year") or row.get("year"),
        "source_provider": _clip(
            row.get("reference_provider") or row.get("source_provider") or row.get("source"),
            160,
        ),
    }


def _state_sha(state: dict[str, Any]) -> str:
    payload = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def _reference_key_sha(row: dict[str, Any]) -> str:
    identity = canonical_identity(row)
    return sha256(identity.encode("utf-8")).hexdigest()


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _probability(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, parsed))


def _normalize_response(payload: Any) -> dict[str, Any] | None:
    root = _as_dict(payload)
    answers = _as_dict(root.get("answers"))

    document = _as_dict(answers.get("document_type"))
    document_choice = str(document.get("choice") or "")
    if document_choice not in DOCUMENT_TYPES:
        return None

    relevance = _as_dict(answers.get("nutrition_relevance"))
    try:
        relevance_score = float(relevance.get("score"))
    except (TypeError, ValueError):
        return None

    ambiguity = _as_dict(answers.get("semantic_ambiguity"))
    ambiguity_probability = _probability(ambiguity.get("noul"))
    if ambiguity_probability is None:
        return None

    usage = _as_dict(root.get("usage"))
    return {
        "model_used": str(root.get("model") or "") or None,
        "document_type": document_choice,
        "document_type_confidence": _probability(document.get("confidence")),
        "document_type_probabilities": _as_dict(document.get("probabilities")),
        "nutrition_relevance_score": relevance_score,
        "nutrition_relevance_confidence": _probability(relevance.get("confidence")),
        "nutrition_relevance_probabilities": _as_dict(relevance.get("probabilities")),
        "semantic_ambiguity_probability": ambiguity_probability,
        "usage": {
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
        },
    }


def evaluate_record(
    row: dict[str, Any],
    config: JevConfig,
    *,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    state = semantic_state(row)
    base = {
        "schema_version": SCHEMA_VERSION,
        "mode": config.mode,
        "provider": "typesafe_jev",
        "ranking_effect": "none",
        "scientific_effect": "none",
        "reference_rank": row.get("reference_rank"),
        "reference_title": row.get("title"),
        "reference_key_sha256": _reference_key_sha(row),
        "input_sha256": _state_sha(state),
        "model_requested": config.model,
    }

    if config.mode == "off":
        return {**base, "status": "disabled"}

    if not config.api_key:
        return {**base, "status": "unconfigured"}

    body = {
        "model": config.model,
        "state": state,
        "questions": {
            "document_type": {
                "type": "choice",
                "instructions": (
                    "Classify document type from supplied bibliographic metadata only. "
                    "Do not infer eligibility, risk of bias, evidence certainty, or recommendations."
                ),
                "criteria": DOCUMENT_TYPES,
            },
            "nutrition_relevance": {
                "type": "score",
                "instructions": (
                    "Score topical nutrition relevance from metadata only. This is a semantic "
                    "description for shadow evaluation, not eligibility or scientific quality."
                ),
                "criteria": [
                    "0: no meaningful nutrition topic is supported",
                    "1: nutrition is peripheral or weakly supported",
                    "2: nutrition is a secondary but clear topic",
                    "3: nutrition is a major topic",
                    "4: nutrition is the central topic",
                ],
            },
            "semantic_ambiguity": {
                "type": "noul",
                "instructions": (
                    "Is the supplied metadata too ambiguous to support a confident semantic "
                    "description? Answer about metadata ambiguity only."
                ),
                "criteria": {
                    "true": "Metadata are materially ambiguous or insufficient.",
                    "false": "Metadata are sufficient for the requested semantic description.",
                },
            },
        },
    }

    client = session or requests.Session()
    started = datetime.now().timestamp()
    try:
        response = client.post(
            f"{config.base_url}/v1/systemone",
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=config.timeout_seconds,
        )
        latency_ms = max(0, round((datetime.now().timestamp() - started) * 1000))
    except requests.Timeout:
        return {**base, "status": "timeout"}
    except requests.RequestException:
        return {**base, "status": "network_error"}

    if not response.ok:
        return {
            **base,
            "status": "provider_error",
            "http_status": response.status_code,
            "latency_ms": latency_ms,
        }

    try:
        normalized = _normalize_response(response.json())
    except ValueError:
        normalized = None
    if normalized is None:
        return {**base, "status": "invalid_response", "latency_ms": latency_ms}

    return {
        **base,
        "status": "ok",
        "latency_ms": latency_ms,
        **normalized,
    }


def run(
    ranking_path: Path,
    output_dir: Path,
    config: JevConfig,
    *,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    if not ranking_path.is_file():
        raise RuntimeError(
            f"Canonical ranking not found: {ranking_path}. Run the deterministic ranker first."
        )

    ranking_sha_before = sha256_file(ranking_path)
    rows = _read_jsonl(ranking_path)
    selected = rows[: config.limit]
    output_dir.mkdir(parents=True, exist_ok=True)

    results = [
        evaluate_record(row, config, session=session)
        for row in selected
    ]
    shadow_path = output_dir / "semantic_shadow.jsonl"
    shadow_sha = _write_jsonl(shadow_path, results)

    counts: dict[str, int] = {}
    for result in results:
        status = str(result.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": _now(),
        "status": "PASS",
        "mode": config.mode,
        "provider": "typesafe_jev",
        "model_requested": config.model,
        "ranking_effect": "none",
        "scientific_effect": "none",
        "canonical_ranking": {
            "path": str(ranking_path),
            "sha256": ranking_sha_before,
            "records_available": len(rows),
            "records_selected": len(selected),
        },
        "counts": counts,
        "outputs": {
            "semantic_shadow": {
                "path": str(shadow_path),
                "sha256": shadow_sha,
            }
        },
        "assertions": {
            "canonical_ranking_not_modified": sha256_file(ranking_path)
            == ranking_sha_before,
            "no_eligibility_decision": True,
            "no_prisma_decision": True,
            "no_quality_or_certainty_decision": True,
            "no_recommendation": True,
        },
    }
    manifest_path = output_dir / "JEV_SHADOW_MANIFEST.json"
    manifest_sha = _write_json(manifest_path, manifest)
    manifest["outputs"]["manifest"] = {
        "path": str(manifest_path),
        "sha256": manifest_sha,
    }
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Jev semantic shadow evaluation without changing NutEV canonical ranking."
    )
    parser.add_argument(
        "--ranking",
        type=Path,
        default=Path("project_output_reference/reference_ranking/reference_ranking.jsonl"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("project_output_reference/jev_semantic_shadow"),
    )
    parser.add_argument("--mode", choices=["off", "shadow"])
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    config = load_config(mode=args.mode, limit=args.limit)
    manifest = run(args.ranking, args.output_dir, config)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
