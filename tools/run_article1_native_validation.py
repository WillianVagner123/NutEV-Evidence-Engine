from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from nutev.science.article1_press import FORMAL_PROVIDERS, ROUTE_ORDER, compile_route_query, load_json, route_specs
from nutev.search.pubmed import PubMedClient
from nutev.search.regional_status import LilacsBVSStatusClient, SciELOStatusClient


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DRAFT = ROOT / "config" / "nutev" / "article1_query_draft_v1.json"
DEFAULT_OUTPUT_ROOT = ROOT / "project_output_reference" / "scientific" / "article1_native_validation"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _client(provider: str):
    if provider == "pubmed":
        return PubMedClient()
    if provider == "lilacs_bvs":
        return LilacsBVSStatusClient()
    if provider == "scielo":
        return SciELOStatusClient()
    raise ValueError(f"unsupported formal provider: {provider}")


def _row_preview(rows: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    return [
        {
            "title": row.get("title") or None,
            "pmid": row.get("pmid") or None,
            "doi": row.get("doi") or None,
            "url": row.get("url") or None,
        }
        for row in rows[:limit]
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Plan or execute Article 1 provider-native pre-freeze validation for "
            "PubMed, LILACS/BVS and SciELO. This never authorizes GF-10, freezes "
            "queries, executes the formal review search, creates eligibility decisions, "
            "or emits PRISMA."
        )
    )
    parser.add_argument("--draft", type=Path, default=DEFAULT_DRAFT)
    parser.add_argument("--provider", choices=FORMAL_PROVIDERS, action="append")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--checkpoint-dir", type=Path, default=ROOT / "07_logs" / "checkpoints")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    if args.limit < 1 or args.limit > 50:
        raise SystemExit("--limit must be between 1 and 50")

    draft = load_json(args.draft)
    specs = route_specs(draft)
    providers = tuple(args.provider or FORMAL_PROVIDERS)
    run_id = "article1_native_validation_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    provider_records: dict[str, Any] = {}
    for provider in providers:
        routes = {
            route_id: {
                "query": compile_route_query(provider, specs[route_id]),
                "status": "PLAN_ONLY_NOT_EXECUTED",
            }
            for route_id in ROUTE_ORDER
        }
        if args.execute:
            client = _client(provider)
            for route_id, record in routes.items():
                result = client.search(
                    record["query"],
                    limit=args.limit,
                    context={
                        "workstream": f"article1_native_validation_{provider}_{route_id}",
                        "checkpoint_dir": args.checkpoint_dir,
                        "resume": False,
                    },
                )
                record.update(
                    {
                        "status": result.status,
                        "error": result.error,
                        "total_found": result.total_found,
                        "total_returned": result.total_returned,
                        "meta": result.meta,
                        "preview": _row_preview(result.rows or []),
                    }
                )
        provider_records[provider] = {
            "role": "formal_bibliographic_provider",
            "routes": routes,
        }

    statuses = [
        route["status"]
        for provider in provider_records.values()
        for route in provider["routes"].values()
    ]
    if not args.execute:
        status = "PLAN_ONLY_NOT_EXECUTED"
    elif statuses and all(value in {"completed", "empty"} for value in statuses):
        status = "TECHNICAL_NATIVE_VALIDATION_COMPLETE_REVIEW_PENDING"
    else:
        status = "TECHNICAL_NATIVE_VALIDATION_INCOMPLETE"

    payload = {
        "schema_version": 1,
        "run_type": "NUTEV_ARTICLE1_PROVIDER_NATIVE_VALIDATION",
        "run_id": run_id,
        "created_at": _now(),
        "status": status,
        "draft_version": draft.get("draft_version"),
        "providers": provider_records,
        "excluded_unavailable_providers": {
            "scopus": "NO_ACCESS_NOT_IN_FORMAL_SET",
            "web_of_science": "NO_ACCESS_NOT_IN_FORMAL_SET",
        },
        "guardrails": {
            "technical_validation_is_not_gf10_authorization": True,
            "query_freeze_performed": False,
            "formal_search_performed": False,
            "prisma_event_emitted": False,
            "eligibility_decisions_created": False,
            "human_review_required_before_gate_change": True,
        },
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload["run_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"

    output = args.output
    if args.execute and output is None:
        output = DEFAULT_OUTPUT_ROOT / run_id / "NATIVE_VALIDATION.json"
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(str(output))
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
