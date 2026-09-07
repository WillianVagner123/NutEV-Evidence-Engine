from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from playwright.sync_api import Page, expect, sync_playwright


BASE_URL = "http://127.0.0.1:8765"
ARTIFACT_DIR = Path("browser_e2e_artifacts")
ROUTES = (
    "/",
    "/search.html",
    "/articles.html",
    "/advanced.html",
    "/ai-context.html",
    "/review-qa.html",
    "/press-review.html",
    "/regional-routes.html",
    "/validation/",
)
EXPECTED_PROVIDERS = {
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
}
EXACT_QUERY = '("Dietary Proteins"[Mesh] OR protein[Title/Abstract]) AND "weight loss"[Title/Abstract]'


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _wait_engine(page: Page) -> None:
    health = page.locator("#health")
    health.wait_for(state="visible", timeout=15_000)
    expect(health).to_contain_text("engine conectado", timeout=15_000)


def _diagnostics(page: Page) -> tuple[list[str], list[str], list[str]]:
    page_errors: list[str] = []
    console_errors: list[str] = []
    resource_errors: list[str] = []

    page.on("pageerror", lambda exc: page_errors.append(str(exc)))

    def on_console(message: Any) -> None:
        if message.type != "error":
            return
        text = str(message.text)
        location = message.location or {}
        url = str(location.get("url") or "")
        if url.endswith("/favicon.ico"):
            return
        line = location.get("lineNumber")
        column = location.get("columnNumber")
        where = f" @ {url}:{line}:{column}" if url else ""
        console_errors.append(text + where)

    def on_response(response: Any) -> None:
        if response.status < 400:
            return
        request = response.request
        if request.resource_type in {"document", "script", "stylesheet"}:
            resource_errors.append(
                f"{request.resource_type} {response.status} {response.url}"
            )

    page.on("console", on_console)
    page.on("response", on_response)
    return page_errors, console_errors, resource_errors


def _assert_clean_diagnostics(
    label: str,
    page_errors: list[str],
    console_errors: list[str],
    resource_errors: list[str],
) -> None:
    failures = [
        *(f"pageerror: {item}" for item in page_errors),
        *(f"console.error: {item}" for item in console_errors),
        *(f"resource: {item}" for item in resource_errors),
    ]
    _assert(not failures, f"{label} browser diagnostics:\n" + "\n".join(failures))


def _route_smoke(browser: Any) -> None:
    for route in ROUTES:
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page_errors, console_errors, resource_errors = _diagnostics(page)
        response = page.goto(BASE_URL + route, wait_until="networkidle", timeout=30_000)
        _assert(response is not None, f"{route}: navigation returned no response")
        _assert(response.status < 400, f"{route}: HTTP {response.status}")
        _assert(page.locator("body").is_visible(), f"{route}: body not visible")
        _assert(page.locator("h1").count() > 0, f"{route}: missing h1")
        _assert(page.locator("h1").first.is_visible(), f"{route}: h1 not visible")
        _assert(
            len(page.locator("body").inner_text().strip()) > 40,
            f"{route}: suspiciously empty page",
        )
        _assert_clean_diagnostics(
            route, page_errors, console_errors, resource_errors
        )
        context.close()


def _open_provider_controls(page: Page) -> None:
    details = page.locator("details.advanced")
    if details.count() and not bool(details.evaluate("el => el.open")):
        details.locator("summary").click()
    page.locator("#providerGrid input[type=checkbox]").first.wait_for(state="visible", timeout=5_000)


def _select_only_pubmed(page: Page) -> None:
    _open_provider_controls(page)
    checkboxes = page.locator("#providerGrid input[type=checkbox]")
    for index in range(checkboxes.count()):
        checkbox = checkboxes.nth(index)
        value = checkbox.get_attribute("value") or ""
        if value == "pubmed":
            if not checkbox.is_checked():
                checkbox.check()
        elif checkbox.is_checked():
            checkbox.uncheck()


def _wait_search_finished(page: Page) -> None:
    expect(page.locator("#searchBtn")).to_be_enabled(timeout=45_000)
    expect(page.locator("#globalSearchBtn")).to_be_enabled(timeout=45_000)


def _search_workspace(browser: Any) -> None:
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()
    page_errors, console_errors, resource_errors = _diagnostics(page)
    page.goto(BASE_URL + "/search.html", wait_until="networkidle", timeout=30_000)
    _wait_engine(page)

    provider_inputs = page.locator("#providerGrid input[type=checkbox]")
    _assert(provider_inputs.count() == 11, f"expected 11 providers, got {provider_inputs.count()}")
    provider_ids = {
        provider_inputs.nth(index).get_attribute("value") or ""
        for index in range(provider_inputs.count())
    }
    _assert(provider_ids == EXPECTED_PROVIDERS, f"provider registry mismatch: {sorted(provider_ids)}")
    _assert("11 fontes conectadas" in page.locator("#searchHint").inner_text(), "search hint does not report 11 sources")
    _assert(page.locator('input[name="searchMode"][value="quick"]').is_checked(), "quick search not default")

    # Quick bounded search against the real server with external network disabled.
    _select_only_pubmed(page)
    page.locator("#question").fill("protein during weight loss in adults with obesity")
    page.locator("#searchBtn").click()
    _wait_search_finished(page)

    # Global search exercises all 11 providers. NUTEV_DISABLE_NETWORK=1 means they
    # must finish explicitly as gaps/skipped rather than pretending zero evidence.
    page.locator("#globalSearchBtn").click()
    _wait_search_finished(page)
    _assert(
        page.locator("#providerGrid input[type=checkbox]:checked").count() == 11,
        "global search did not activate all providers",
    )

    # Advanced strategy builder: PCC/PICO/PECO must all materialize correctly.
    page.locator('input[name="searchMode"][value="advanced"]').check()
    page.locator("#strategyBuilder").wait_for(state="visible")
    _assert(page.locator("#conceptBuilder .concept-card").count() == 3, "PCC must have 3 concept cards")
    page.locator("#frameworkSelect").select_option("PICO")
    _assert(page.locator("#conceptBuilder .concept-card").count() == 4, "PICO must have 4 concept cards")
    page.locator("#frameworkSelect").select_option("PECO")
    _assert(page.locator("#conceptBuilder .concept-card").count() == 4, "PECO must have 4 concept cards")
    page.locator("#frameworkSelect").select_option("PCC")
    page.locator("#conceptBuilder .concept-terms").nth(0).fill("free:adults\nmesh:Obesity")
    page.locator("#conceptBuilder .concept-terms").nth(1).fill("free:protein\ndecs:Proteínas")
    page.locator("#conceptBuilder .concept-terms").nth(2).fill("free:weight loss")
    page.locator("#compileStrategyBtn").click()
    page.locator("#strategyPreview").wait_for(state="visible", timeout=15_000)
    _assert("Preview auditável" in page.locator("#strategyPreview").inner_text(), "advanced preview missing")

    # Exact mode: only PubMed selected so one literal string is sufficient.
    page.locator('input[name="searchMode"][value="exact"]').check()
    _select_only_pubmed(page)
    page.locator("#strategyId").fill("predeploy-browser-exact")
    page.locator("#strategyVersion").fill("v1.0")
    exact_box = page.locator('#exactQueryBuilder textarea[data-provider="pubmed"]')
    exact_box.wait_for(state="visible")
    exact_box.fill(EXACT_QUERY)
    page.locator("#compileStrategyBtn").click()
    page.locator("#strategyPreview").wait_for(state="visible", timeout=15_000)
    preview_text = page.locator("#strategyPreview").inner_text()
    _assert("predeploy-browser-exact" in preview_text, "exact strategy id missing from preview")
    _assert("v1.0" in preview_text, "exact strategy version missing from preview")
    exact_preview = page.locator("#strategyPreview details.compiled-query").first
    exact_preview.locator("summary").click()
    exact_code = exact_preview.locator("code")
    exact_code.wait_for(state="visible", timeout=5_000)
    _assert(exact_code.inner_text() == EXACT_QUERY, "literal exact query changed in preview")

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(ARTIFACT_DIR / "search-desktop.png"), full_page=True)

    # Persisted quick/global runs must be visible in history with their gap state.
    page.goto(BASE_URL + "/search.html?view=history", wait_until="networkidle", timeout=30_000)
    page.locator("#historyList .history-item").first.wait_for(state="visible", timeout=15_000)
    page.locator("#historyList .history-card").nth(1).wait_for(state="visible", timeout=15_000)
    _assert(
        page.locator("#historyList .history-card").count() >= 2,
        "history did not retain both pre-deploy searches",
    )
    history_text = page.locator("#historyList").inner_text().casefold()
    _assert("lacuna" in history_text, "history does not surface provider/audit gaps")

    _assert_clean_diagnostics(
        "search workspace", page_errors, console_errors, resource_errors
    )
    context.close()


def _mobile_smoke(browser: Any) -> None:
    context = browser.new_context(viewport={"width": 390, "height": 844})
    page = context.new_page()
    page_errors, console_errors, resource_errors = _diagnostics(page)
    page.goto(BASE_URL + "/search.html", wait_until="networkidle", timeout=30_000)
    _wait_engine(page)
    page.locator("#searchBtn").wait_for(state="visible")
    overflow = page.evaluate(
        "Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - window.innerWidth"
    )
    _assert(float(overflow) <= 2.0, f"mobile horizontal overflow detected: {overflow}px")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(ARTIFACT_DIR / "search-mobile.png"), full_page=True)
    _assert_clean_diagnostics(
        "mobile search", page_errors, console_errors, resource_errors
    )
    context.close()


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            _route_smoke(browser)
            _search_workspace(browser)
            _mobile_smoke(browser)
        finally:
            browser.close()
    print("PRE_DEPLOY_BROWSER_E2E_PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"PRE_DEPLOY_BROWSER_E2E_FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
