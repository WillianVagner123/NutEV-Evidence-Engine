from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "apps" / "nutev-web"
SRC_ROOT = ROOT / "src"
if str(WEB_ROOT) not in sys.path:
    sys.path.insert(0, str(WEB_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from query_compiler import compile_query_plan
from search_adapter import PROVIDER_LABELS, PROVIDER_ORDER


EXPECTED_PROVIDERS = (
    "pubmed",
    "europepmc",
    "openalex",
    "crossref",
    "doaj",
    "semantic_scholar",
    "google_pse",
    "brave",
    "serpapi",
    "lilacs_bvs_native",
    "scielo_native",
)
CRITICAL_WEB_FILES = (
    "index.html",
    "search.html",
    "articles.html",
    "advanced.html",
    "product-ui.js",
    "app.js",
)
OPTIONAL_PROVIDER_ENV = {
    "google_pse": ("GOOGLE_API_KEY", "GOOGLE_CSE_ID"),
    "brave": ("BRAVE_API_KEY",),
    "serpapi": ("SERPAPI_API_KEY",),
}
QUESTION = "protein during weight loss in adults with obesity"
EXACT_QUERY = '("Dietary Proteins"[Mesh] OR protein[Title/Abstract]) AND ("Weight Loss"[Mesh] OR "weight loss"[Title/Abstract])'


def _check(name: str, status: str, detail: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"name": name, "status": status, "detail": detail}
    payload.update(extra)
    return payload


def _structured_strategy() -> dict[str, Any]:
    return {
        "framework": "PICO",
        "concepts": [
            {"label": "Population", "terms": ["free:adults", "mesh:Obesity"]},
            {"label": "Intervention", "terms": ["free:higher protein"]},
            {"label": "Comparator", "terms": ["free:standard protein"]},
            {"label": "Outcome", "terms": ["free:lean mass"]},
        ],
    }


def build_runtime_report(
    *,
    web_root: Path = WEB_ROOT,
    output_root: Path | None = None,
    write_probe: bool = False,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    actual_providers = tuple(PROVIDER_ORDER)
    if actual_providers == EXPECTED_PROVIDERS and len(set(actual_providers)) == len(actual_providers):
        checks.append(_check("provider_registry", "PASS", "11 public providers are registered in canonical order", provider_count=len(actual_providers)))
    else:
        checks.append(_check("provider_registry", "FAIL", "public provider registry differs from the pre-deploy contract", expected=list(EXPECTED_PROVIDERS), actual=list(actual_providers)))

    missing_labels = [provider for provider in actual_providers if not str(PROVIDER_LABELS.get(provider) or "").strip()]
    checks.append(
        _check(
            "provider_labels",
            "FAIL" if missing_labels else "PASS",
            "all public providers have UI labels" if not missing_labels else "providers without UI labels: " + ", ".join(missing_labels),
        )
    )

    missing_files = [name for name in CRITICAL_WEB_FILES if not (web_root / name).is_file() or (web_root / name).stat().st_size <= 0]
    checks.append(
        _check(
            "critical_web_surfaces",
            "FAIL" if missing_files else "PASS",
            "critical public web surfaces are materialized" if not missing_files else "missing/empty critical files: " + ", ".join(missing_files),
            checked=list(CRITICAL_WEB_FILES),
        )
    )

    config_path = ROOT / "config" / "reference_mode.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("root is not an object")
        checks.append(_check("reference_mode_config", "PASS", "config/reference_mode.json parses as an object"))
    except Exception as exc:
        checks.append(_check("reference_mode_config", "FAIL", f"reference mode config invalid: {type(exc).__name__}: {exc}"))

    try:
        quick = compile_query_plan(QUESTION, list(actual_providers), None)
        quick_queries = quick.get("provider_queries") or {}
        missing = [provider for provider in actual_providers if provider not in quick_queries]
        if quick.get("mode") != "natural_language" or missing:
            raise ValueError(f"mode={quick.get('mode')!r}, providers_without_query={missing}")
        checks.append(_check("quick_query_compiler", "PASS", "quick search compiles for all 11 providers"))
    except Exception as exc:
        checks.append(_check("quick_query_compiler", "FAIL", f"quick query compilation failed: {type(exc).__name__}: {exc}"))

    try:
        structured = compile_query_plan(QUESTION, list(actual_providers), _structured_strategy())
        structured_queries = structured.get("provider_queries") or {}
        missing = [provider for provider in actual_providers if provider not in structured_queries]
        if structured.get("mode") != "structured_review" or missing:
            raise ValueError(f"mode={structured.get('mode')!r}, providers_without_query={missing}")
        checks.append(_check("structured_query_compiler", "PASS", "PICO search compiles for all 11 providers"))
    except Exception as exc:
        checks.append(_check("structured_query_compiler", "FAIL", f"structured query compilation failed: {type(exc).__name__}: {exc}"))

    try:
        exact = compile_query_plan(
            QUESTION,
            ["pubmed"],
            {
                "mode": "exact",
                "strategy_id": "runtime-readiness",
                "strategy_version": "v1.0",
                "run_class": "DEVELOPMENT",
                "provider_queries": {"pubmed": EXACT_QUERY},
            },
        )
        compiled_exact = str(((exact.get("provider_queries") or {}).get("pubmed") or {}).get("query") or "")
        if exact.get("mode") != "exact_review" or compiled_exact != EXACT_QUERY:
            raise ValueError("exact query was changed or exact mode was not preserved")
        checks.append(_check("exact_query_compiler", "PASS", "exact PubMed strategy remains literal and versioned"))
    except Exception as exc:
        checks.append(_check("exact_query_compiler", "FAIL", f"exact query compilation failed: {type(exc).__name__}: {exc}"))

    build_info_path = web_root / "build-info.json"
    if build_info_path.is_file():
        try:
            build_info = json.loads(build_info_path.read_text(encoding="utf-8"))
            commit = str(build_info.get("build_commit") or "").strip() if isinstance(build_info, dict) else ""
            if not commit or commit == "unknown":
                raise ValueError("build_commit missing or unknown")
            checks.append(_check("build_identity", "PASS", "image-owned build identity is materialized", build_commit=commit))
        except Exception as exc:
            checks.append(_check("build_identity", "FAIL", f"build-info.json invalid: {type(exc).__name__}: {exc}"))
    else:
        checks.append(_check("build_identity", "WARN", "build-info.json is generated by the production image and is not present in the source checkout"))

    credential_state: dict[str, str] = {}
    for provider, keys in OPTIONAL_PROVIDER_ENV.items():
        missing = [key for key in keys if not os.environ.get(key)]
        credential_state[provider] = "configured" if not missing else "skipped_config"
    missing_optional = [provider for provider, state in credential_state.items() if state != "configured"]
    checks.append(
        _check(
            "optional_provider_credentials",
            "WARN" if missing_optional else "PASS",
            "optional web providers without credentials will be explicit skipped gaps" if missing_optional else "all optional web provider credentials are configured",
            providers=credential_state,
        )
    )

    root = (output_root or (ROOT / "project_output_reference")).resolve()
    if write_probe:
        try:
            root.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile(prefix=".nutev-runtime-", suffix=".tmp", dir=root, delete=False) as handle:
                handle.write(b"runtime-write-probe\n")
                handle.flush()
                os.fsync(handle.fileno())
                probe_path = Path(handle.name)
            probe_path.unlink()
            checks.append(_check("persistent_output_write", "PASS", "persistent output root is writable by the runtime user"))
        except Exception as exc:
            checks.append(_check("persistent_output_write", "FAIL", f"persistent output write probe failed: {type(exc).__name__}: {exc}"))
    else:
        checks.append(_check("persistent_output_write", "WARN", "write probe not requested"))

    failures = [item for item in checks if item["status"] == "FAIL"]
    warnings = [item for item in checks if item["status"] == "WARN"]
    status = "NOT_READY" if failures else ("READY_WITH_WARNINGS" if warnings else "READY")
    return {
        "schema_version": 1,
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provider_count": len(actual_providers),
        "checks": checks,
        "failures": [item["name"] for item in failures],
        "warnings": [item["name"] for item in warnings],
        "semantics": "offline operational readiness only; no external provider is queried and no scientific inclusion/quality state is advanced",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the NutEV pre-deploy runtime contract without external network calls.")
    parser.add_argument("--output-root", type=Path, default=ROOT / "project_output_reference")
    parser.add_argument("--write-probe", action="store_true", help="Create and remove one tiny file in the persistent output root.")
    parser.add_argument("--json", action="store_true", help="Emit the report as JSON.")
    args = parser.parse_args()

    report = build_runtime_report(output_root=args.output_root, write_probe=args.write_probe)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(report["status"])
        for item in report["checks"]:
            print(f"{item['status']:>4}  {item['name']}: {item['detail']}")
    return 1 if report["status"] == "NOT_READY" else 0


if __name__ == "__main__":
    raise SystemExit(main())
