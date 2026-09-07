from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from playwright.sync_api import Page, expect, sync_playwright


BASE_URL = "http://127.0.0.1:8765"
ARTIFACT_DIR = Path("browser_e2e_artifacts")
EXACT_QUERY = '("Dietary Proteins"[Mesh] OR protein[Title/Abstract]) AND "weight loss"[Title/Abstract]'
FRAMEWORK_TERMS = {
    "PCC": (
        "free:adults with obesity\nmesh:Obesity",
        "free:protein\ndecs:Proteínas",
        "free:weight loss",
    ),
    "PICO": (
        "free:adults with obesity\nmesh:Obesity",
        "free:higher protein intake",
        "free:standard protein diet",
        "free:lean mass",
    ),
    "PECO": (
        "free:adults with obesity\nmesh:Obesity",
        "free:severe energy restriction",
        "free:higher protein intake",
        "free:lean mass",
    ),
}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _wait_engine(page: Page) -> None:
    health = page.locator("#health")
    health.wait_for(state="visible", timeout=15_000)
    expect(health).to_contain_text("engine conectado", timeout=15_000)


def _open_provider_controls(page: Page) -> None:
    details = page.locator("details.advanced")
    if details.count() and not bool(details.evaluate("el => el.open")):
        details.locator("summary").click()
    page.locator("#providerGrid input[type=checkbox]").first.wait_for(
        state="visible", timeout=5_000
    )


def _select_only_pubmed(page: Page) -> None:
    _open_provider_controls(page)
    checkboxes = page.locator("#providerGrid input[type=checkbox]")
    for index in range(checkboxes.count()):
        checkbox = checkboxes.nth(index)
        is_pubmed = (checkbox.get_attribute("value") or "") == "pubmed"
        if is_pubmed and not checkbox.is_checked():
            checkbox.check()
        elif not is_pubmed and checkbox.is_checked():
            checkbox.uncheck()


def _wait_search_finished(page: Page) -> None:
    expect(page.locator("#searchBtn")).to_be_enabled(timeout=45_000)
    expect(page.locator("#globalSearchBtn")).to_be_enabled(timeout=45_000)
    expect(page.locator("#summary")).to_be_visible(timeout=45_000)


def _run_bounded(page: Page) -> None:
    _select_only_pubmed(page)
    page.locator("#searchBtn").click()
    _wait_search_finished(page)


def _run_global(page: Page, *, exact: bool = False) -> None:
    before = page.locator("#providerGrid input[type=checkbox]:checked").count()
    page.locator("#globalSearchBtn").click()
    _wait_search_finished(page)
    after = page.locator("#providerGrid input[type=checkbox]:checked").count()
    if exact:
        _assert(after == before == 1, "exact global changed the explicitly selected provider set")
    else:
        _assert(after == 11, f"global structured search selected {after} providers instead of 11")


def _set_framework(page: Page, framework: str) -> None:
    page.locator('input[name="searchMode"][value="advanced"]').check()
    page.locator("#frameworkSelect").select_option(framework)
    terms = FRAMEWORK_TERMS[framework]
    cards = page.locator("#conceptBuilder .concept-card")
    _assert(cards.count() == len(terms), f"{framework}: expected {len(terms)} cards, got {cards.count()}")
    for index, value in enumerate(terms):
        cards.nth(index).locator(".concept-terms").fill(value)


def _assert_provider_gap_summary(page: Page, label: str) -> None:
    text = page.locator("#summary").inner_text().casefold()
    _assert("lacuna" in text, f"{label}: provider gaps were not surfaced in the result summary")


def _run_structured_matrix(page: Page) -> int:
    runs = 0
    for framework in ("PCC", "PICO", "PECO"):
        _set_framework(page, framework)
        _run_bounded(page)
        _assert_provider_gap_summary(page, f"{framework} bounded")
        runs += 1

        _run_global(page)
        _assert_provider_gap_summary(page, f"{framework} global")
        runs += 1
    return runs


def _run_exact_matrix(page: Page) -> int:
    page.locator('input[name="searchMode"][value="exact"]').check()
    _select_only_pubmed(page)
    page.locator("#strategyId").fill("predeploy-browser-exact-execution")
    page.locator("#strategyVersion").fill("v1.0")
    exact_box = page.locator('#exactQueryBuilder textarea[data-provider="pubmed"]')
    exact_box.wait_for(state="visible", timeout=5_000)
    exact_box.fill(EXACT_QUERY)

    _run_bounded(page)
    summary = page.locator("#summary").inner_text()
    _assert("Estratégia exata" in summary, "exact bounded did not render exact-strategy audit state")
    _assert_provider_gap_summary(page, "Exact bounded")

    _run_global(page, exact=True)
    summary = page.locator("#summary").inner_text()
    _assert("Estratégia exata" in summary, "exact global did not render exact-strategy audit state")
    _assert("Busca sem teto interno" in summary, "exact global did not surface no-internal-cap semantics")
    _assert_provider_gap_summary(page, "Exact global")
    return 2


def _browser_diagnostics(page: Page) -> tuple[list[str], list[str], list[str]]:
    page_errors: list[str] = []
    console_errors: list[str] = []
    resource_errors: list[str] = []
    page.on("pageerror", lambda exc: page_errors.append(str(exc)))

    def on_console(message: Any) -> None:
        if message.type == "error" and "favicon.ico" not in str(message.text):
            console_errors.append(str(message.text))

    def on_response(response: Any) -> None:
        if response.status >= 400 and response.request.resource_type in {
            "document",
            "script",
            "stylesheet",
        }:
            resource_errors.append(
                f"{response.request.resource_type} {response.status} {response.url}"
            )

    page.on("console", on_console)
    page.on("response", on_response)
    return page_errors, console_errors, resource_errors


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page_errors, console_errors, resource_errors = _browser_diagnostics(page)
        try:
            page.goto(BASE_URL + "/search.html", wait_until="networkidle", timeout=30_000)
            _wait_engine(page)
            page.locator("#question").fill(
                "protein adequacy during severe energy restriction in adults with obesity"
            )
            structured_runs = _run_structured_matrix(page)
            exact_runs = _run_exact_matrix(page)
            _assert(structured_runs == 6, f"expected 6 structured runs, got {structured_runs}")
            _assert(exact_runs == 2, f"expected 2 exact runs, got {exact_runs}")

            page.screenshot(
                path=str(ARTIFACT_DIR / "search-execution-matrix.png"),
                full_page=True,
            )

            page.goto(
                BASE_URL + "/search.html?view=history",
                wait_until="networkidle",
                timeout=30_000,
            )
            page.locator("#historyList .history-card").first.wait_for(
                state="visible", timeout=15_000
            )
            history_count = page.locator("#historyList .history-card").count()
            _assert(
                history_count >= 10,
                f"expected at least 10 persisted UI search runs including Quick, got {history_count}",
            )
            history_text = page.locator("#historyList").inner_text().casefold()
            _assert("lacuna" in history_text, "history lost provider-gap semantics")

            failures = [
                *(f"pageerror: {item}" for item in page_errors),
                *(f"console.error: {item}" for item in console_errors),
                *(f"resource: {item}" for item in resource_errors),
            ]
            _assert(not failures, "search UI execution diagnostics:\n" + "\n".join(failures))
        finally:
            context.close()
            browser.close()

    print("PRE_DEPLOY_SEARCH_UI_EXECUTION_MATRIX_PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            f"PRE_DEPLOY_SEARCH_UI_EXECUTION_MATRIX_FAIL: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        raise
