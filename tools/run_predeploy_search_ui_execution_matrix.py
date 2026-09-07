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


def _start_search(page: Page, selector: str) -> dict[str, Any]:
    with page.expect_response(
        lambda response: response.url.endswith("/api/search/jobs")
        and response.request.method == "POST",
        timeout=8_000,
    ) as pending:
        page.locator(selector).click()
    started = pending.value
    _assert(started.status == 202, f"{selector}: search job start HTTP {started.status}")
    job = started.json()
    job_id = str(job.get("job_id") or "")
    _assert(bool(job_id), f"{selector}: search job did not return job_id")
    _wait_search_finished(page)
    terminal = page.evaluate(
        """async (jobId) => {
          const response = await fetch(`/api/search/jobs/${encodeURIComponent(jobId)}`, {cache:'no-store'});
          return {status: response.status, payload: await response.json()};
        }""",
        job_id,
    )
    _assert(terminal["status"] == 200, f"{selector}: terminal job HTTP {terminal['status']}")
    payload = terminal["payload"]
    _assert(payload.get("status") == "completed", f"{selector}: terminal job is {payload.get('status')}")
    result = payload.get("result")
    _assert(isinstance(result, dict), f"{selector}: completed job has no persisted result")
    return result


def _run_bounded(page: Page) -> dict[str, Any]:
    _select_only_pubmed(page)
    return _start_search(page, "#searchBtn")


def _run_global(page: Page, *, exact: bool = False) -> dict[str, Any]:
    before = page.locator("#providerGrid input[type=checkbox]:checked").count()
    result = _start_search(page, "#globalSearchBtn")
    after = page.locator("#providerGrid input[type=checkbox]:checked").count()
    if exact:
        _assert(after == before == 1, "exact global changed the explicitly selected provider set")
    else:
        _assert(after == 11, f"global search selected {after} providers instead of 11")
    return result


def _assert_provider_gap_summary(page: Page, label: str) -> None:
    text = page.locator("#summary").inner_text().casefold()
    _assert("lacuna" in text, f"{label}: provider gaps were not surfaced in the result summary")


def _assert_visible_identity(page: Page, expected: str, label: str) -> None:
    expect(page.locator("#summary")).to_contain_text(expected, timeout=5_000)
    text = page.locator("#summary").inner_text()
    _assert(expected in text, f"{label}: visible execution identity missing. Summary: {text[:500]}")


def _assert_mode(result: dict[str, Any], expected: str, label: str) -> None:
    actual = str(result.get("search_mode") or "")
    _assert(actual == expected, f"{label}: expected search_mode={expected}, got {actual}")


def _run_quick_matrix(page: Page) -> int:
    page.locator('input[name="searchMode"][value="quick"]').check()
    bounded = _run_bounded(page)
    _assert_mode(bounded, "interactive_bounded", "Quick bounded")
    _assert_visible_identity(page, "Busca rápida · limitada", "Quick bounded")
    _assert_provider_gap_summary(page, "Quick bounded")

    global_result = _run_global(page)
    _assert_mode(global_result, "global_exhaustive", "Quick global")
    _assert(global_result.get("exhaustive_requested") is True, "Quick global lost exhaustive_requested")
    _assert_visible_identity(page, "Busca rápida · cobertura máxima", "Quick global")
    _assert_provider_gap_summary(page, "Quick global")
    return 2


def _set_framework(page: Page, framework: str) -> None:
    page.locator('input[name="searchMode"][value="advanced"]').check()
    page.locator("#frameworkSelect").select_option(framework)
    terms = FRAMEWORK_TERMS[framework]
    cards = page.locator("#conceptBuilder .concept-card")
    _assert(cards.count() == len(terms), f"{framework}: expected {len(terms)} cards, got {cards.count()}")
    for index, value in enumerate(terms):
        cards.nth(index).locator(".concept-terms").fill(value)


def _run_structured_matrix(page: Page) -> int:
    runs = 0
    for framework in ("PCC", "PICO", "PECO"):
        _set_framework(page, framework)
        bounded = _run_bounded(page)
        _assert_mode(bounded, "structured_review_bounded", f"{framework} bounded")
        _assert((bounded.get("query_plan") or {}).get("framework") == framework, f"{framework} bounded lost framework audit plan")
        _assert_visible_identity(page, f"Busca avançada · {framework}", f"{framework} bounded")
        _assert_provider_gap_summary(page, f"{framework} bounded")
        runs += 1

        global_result = _run_global(page)
        _assert_mode(global_result, "structured_review_global_exhaustive", f"{framework} global")
        _assert(global_result.get("exhaustive_requested") is True, f"{framework} global lost exhaustive_requested")
        _assert((global_result.get("query_plan") or {}).get("framework") == framework, f"{framework} global lost framework audit plan")
        _assert_visible_identity(page, f"Busca avançada · {framework} · cobertura máxima", f"{framework} global")
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

    bounded = _run_bounded(page)
    _assert_mode(bounded, "exact_review_bounded", "Exact bounded")
    plan = bounded.get("query_plan") or {}
    _assert(plan.get("mode") == "exact_review", f"Exact bounded query plan mode is {plan.get('mode')}")
    _assert(plan.get("strategy_id") == "predeploy-browser-exact-execution", "Exact bounded lost strategy_id")
    _assert(plan.get("strategy_version") == "v1.0", "Exact bounded lost strategy_version")
    literal = ((plan.get("provider_queries") or {}).get("pubmed") or {}).get("query")
    _assert(literal == EXACT_QUERY, "Exact bounded rewrote the literal PubMed query")
    _assert_visible_identity(page, "Estratégia exata · predeploy-browser-exact-execution · v1.0", "Exact bounded")
    _assert_provider_gap_summary(page, "Exact bounded")

    global_result = _run_global(page, exact=True)
    _assert_mode(global_result, "exact_review_global_exhaustive", "Exact global")
    _assert(global_result.get("exhaustive_requested") is True, "Exact global lost exhaustive_requested")
    plan = global_result.get("query_plan") or {}
    literal = ((plan.get("provider_queries") or {}).get("pubmed") or {}).get("query")
    _assert(literal == EXACT_QUERY, "Exact global rewrote the literal PubMed query")
    _assert_visible_identity(page, "Estratégia exata · predeploy-browser-exact-execution · v1.0 · cobertura máxima", "Exact global")
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
        if response.status >= 400 and response.request.resource_type in {"document", "script", "stylesheet"}:
            resource_errors.append(f"{response.request.resource_type} {response.status} {response.url}")

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
            page.locator("#question").fill("protein adequacy during severe energy restriction in adults with obesity")

            quick_runs = _run_quick_matrix(page)
            structured_runs = _run_structured_matrix(page)
            exact_runs = _run_exact_matrix(page)
            _assert(quick_runs == 2, f"expected 2 Quick runs, got {quick_runs}")
            _assert(structured_runs == 6, f"expected 6 structured runs, got {structured_runs}")
            _assert(exact_runs == 2, f"expected 2 exact runs, got {exact_runs}")

            page.screenshot(path=str(ARTIFACT_DIR / "search-execution-matrix.png"), full_page=True)
            page.goto(BASE_URL + "/search.html?view=history", wait_until="networkidle", timeout=30_000)
            page.locator("#historyList .history-card").first.wait_for(state="visible", timeout=15_000)
            history_count = page.locator("#historyList .history-card").count()
            _assert(history_count >= 10, f"expected 10 persisted UI search runs in this browser session, got {history_count}")
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
        print(f"PRE_DEPLOY_SEARCH_UI_EXECUTION_MATRIX_FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
