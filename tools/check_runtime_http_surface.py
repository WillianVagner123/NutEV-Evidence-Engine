from __future__ import annotations

import argparse
import json
from typing import Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen


EXPECTED_PROVIDER_IDS = (
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


def _get(base_url: str, path: str, *, timeout: float = 5.0) -> tuple[int, bytes, str]:
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    request = Request(url, headers={"Accept": "application/json,text/html;q=0.9,*/*;q=0.1"})
    with urlopen(request, timeout=timeout) as response:
        return int(response.status), response.read(), str(response.headers.get("Content-Type") or "")


def _get_json(base_url: str, path: str, *, timeout: float = 5.0) -> dict[str, Any]:
    status, body, _ = _get(base_url, path, timeout=timeout)
    if status != 200:
        raise ValueError(f"{path} returned HTTP {status}")
    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} did not return a JSON object")
    return payload


def validate_runtime_payloads(
    *,
    health: dict[str, Any],
    version: dict[str, Any],
    providers: dict[str, Any],
    expected_commit: str,
) -> list[str]:
    failures: list[str] = []

    if health.get("status") != "ok":
        failures.append("health.status must be 'ok'")

    actual_commit = str(version.get("commit") or "").strip()
    if not actual_commit:
        failures.append("version.commit is missing")
    elif actual_commit != expected_commit:
        failures.append(f"version.commit mismatch: expected {expected_commit}, got {actual_commit}")

    rows = providers.get("providers")
    if not isinstance(rows, list):
        failures.append("providers.providers must be a list")
    else:
        ids: list[str] = []
        labels_missing: list[str] = []
        for row in rows:
            if not isinstance(row, dict):
                failures.append("providers.providers contains a non-object entry")
                continue
            provider_id = str(row.get("id") or "").strip()
            if provider_id:
                ids.append(provider_id)
                if not str(row.get("label") or "").strip():
                    labels_missing.append(provider_id)
            else:
                failures.append("provider entry without id")
        if tuple(ids) != EXPECTED_PROVIDER_IDS:
            failures.append(
                "provider ids/order mismatch: "
                + json.dumps({"expected": EXPECTED_PROVIDER_IDS, "actual": ids}, ensure_ascii=False)
            )
        if len(ids) != len(set(ids)):
            failures.append("provider ids contain duplicates")
        if labels_missing:
            failures.append("provider labels missing: " + ", ".join(labels_missing))

    return failures


def check_runtime_http_surface(base_url: str, expected_commit: str, *, timeout: float = 5.0) -> dict[str, Any]:
    health = _get_json(base_url, "/api/health", timeout=timeout)
    version = _get_json(base_url, "/api/version", timeout=timeout)
    providers = _get_json(base_url, "/api/providers", timeout=timeout)

    page_checks: dict[str, dict[str, Any]] = {}
    for path in ("/search.html", "/articles.html"):
        status, body, content_type = _get(base_url, path, timeout=timeout)
        text = body.decode("utf-8", errors="replace")
        page_checks[path] = {
            "status": status,
            "bytes": len(body),
            "content_type": content_type,
            "contains_nutev": "nutev" in text.casefold(),
        }

    failures = validate_runtime_payloads(
        health=health,
        version=version,
        providers=providers,
        expected_commit=expected_commit,
    )
    for path, item in page_checks.items():
        if item["status"] != 200:
            failures.append(f"{path} returned HTTP {item['status']}")
        if item["bytes"] <= 0:
            failures.append(f"{path} returned an empty body")
        if not item["contains_nutev"]:
            failures.append(f"{path} does not contain the NutEV product marker")

    return {
        "status": "PASS" if not failures else "FAIL",
        "base_url": base_url.rstrip("/"),
        "expected_commit": expected_commit,
        "actual_commit": str(version.get("commit") or ""),
        "provider_count": len(providers.get("providers") or []),
        "provider_ids": [
            str(item.get("id") or "")
            for item in (providers.get("providers") or [])
            if isinstance(item, dict)
        ],
        "pages": page_checks,
        "failures": failures,
        "semantics": "live local HTTP surface validation only; no external scientific provider is queried",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the running NutEV HTTP surface without external provider calls.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        report = check_runtime_http_surface(args.base_url, args.expected_commit, timeout=args.timeout)
    except Exception as exc:
        report = {
            "status": "FAIL",
            "base_url": args.base_url.rstrip("/"),
            "expected_commit": args.expected_commit,
            "failures": [f"{type(exc).__name__}: {exc}"],
            "semantics": "live local HTTP surface validation only; no external scientific provider is queried",
        }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(report["status"])
        for failure in report.get("failures") or []:
            print(f"FAIL  {failure}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
