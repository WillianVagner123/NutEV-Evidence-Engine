from __future__ import annotations

from pathlib import Path

from tools.check_predeploy_runtime_contract import (
    CRITICAL_WEB_FILES,
    EXPECTED_PROVIDERS,
    build_runtime_report,
)


def _check(report: dict[str, object], name: str) -> dict[str, object]:
    for item in report["checks"]:  # type: ignore[index]
        if item["name"] == name:
            return item
    raise AssertionError(name)


def test_repository_runtime_contract_has_no_failures() -> None:
    report = build_runtime_report(write_probe=False)

    assert report["status"] in {"READY", "READY_WITH_WARNINGS"}
    assert report["failures"] == []
    assert report["provider_count"] == 11
    assert tuple(EXPECTED_PROVIDERS) == (
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
    assert _check(report, "quick_query_compiler")["status"] == "PASS"
    assert _check(report, "structured_query_compiler")["status"] == "PASS"
    assert _check(report, "exact_query_compiler")["status"] == "PASS"


def test_runtime_contract_write_probe_is_non_destructive(tmp_path: Path) -> None:
    report = build_runtime_report(output_root=tmp_path, write_probe=True)

    assert report["status"] in {"READY", "READY_WITH_WARNINGS"}
    assert _check(report, "persistent_output_write")["status"] == "PASS"
    assert list(tmp_path.iterdir()) == []


def test_runtime_contract_fails_closed_when_critical_web_surface_is_missing(tmp_path: Path) -> None:
    web_root = tmp_path / "web"
    web_root.mkdir()
    for name in CRITICAL_WEB_FILES[:-1]:
        (web_root / name).write_text("ok\n", encoding="utf-8")

    report = build_runtime_report(web_root=web_root, output_root=tmp_path / "output")

    assert report["status"] == "NOT_READY"
    assert "critical_web_surfaces" in report["failures"]
    detail = str(_check(report, "critical_web_surfaces")["detail"])
    assert CRITICAL_WEB_FILES[-1] in detail


def test_optional_provider_credentials_are_warnings_not_false_absence(monkeypatch) -> None:
    for key in ("GOOGLE_API_KEY", "GOOGLE_CSE_ID", "BRAVE_API_KEY", "SERPAPI_API_KEY"):
        monkeypatch.delenv(key, raising=False)

    report = build_runtime_report(write_probe=False)
    credential_check = _check(report, "optional_provider_credentials")

    assert credential_check["status"] == "WARN"
    assert credential_check["providers"] == {
        "google_pse": "skipped_config",
        "brave": "skipped_config",
        "serpapi": "skipped_config",
    }
    assert report["status"] == "READY_WITH_WARNINGS"
