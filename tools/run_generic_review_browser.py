"""Browser proof for generic application-scoped Review against synthetic pilot fixtures only."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from tools.pilot_closeout_fixture import pilot_server


def run(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, str]] = []
    network: list[dict[str, object]] = []
    diagnostics: list[str] = []

    def passed(name: str) -> None:
        checks.append({"check": name, "status": "PASS"})

    with pilot_server() as (base, data, root), sync_playwright() as playwright:
        executable = os.environ.get("NUTEV_CHROMIUM_EXECUTABLE")
        browser = playwright.chromium.launch(
            **({"executable_path": executable} if executable else {}),
            args=["--no-sandbox"],
        )
        contexts = []

        def new_context():
            context = browser.new_context(viewport={"width": 1366, "height": 900})
            context.route(
                "**/*",
                lambda route: route.continue_()
                if route.request.url.startswith(base)
                else route.abort(),
            )
            contexts.append(context)
            return context

        def page_in(context):
            page = context.new_page()
            page.on("pageerror", lambda error: diagnostics.append(str(error)))
            page.on(
                "request",
                lambda request: network.append(
                    {"event": "request", "url": request.url, "method": request.method}
                ),
            )
            page.on(
                "requestfailed",
                lambda request: network.append(
                    {"event": "failed", "url": request.url, "reason": request.failure}
                ),
            )
            return page

        def login_and_select(page, label: str, project_index: int = 0) -> None:
            user = data["users"][label]
            page.goto(base + "/login.html", wait_until="domcontentloaded")
            page.locator("#loginEmail").fill(user["email"])
            page.locator("#loginPassword").fill(user["password"])
            page.locator("#loginSubmit").click()
            page.wait_for_url(base + "/", timeout=10000)
            expect(page.locator("#nutevWorkspaceSelect")).to_be_visible()
            with page.expect_navigation(wait_until="domcontentloaded"):
                page.locator("#nutevWorkspaceSelect").select_option(user["workspace_id"])
            with page.expect_navigation(wait_until="domcontentloaded"):
                page.locator("#nutevProjectSelect").select_option(user["projects"][project_index])
            expect(page.locator("#nutevProjectSelect")).to_have_value(user["projects"][project_index])

        try:
            anonymous = new_context()
            response = anonymous.request.get(base + "/api/review")
            assert response.status == 401, response.text()
            passed("generic_review_unauthenticated_fails_closed")

            context_a = new_context()
            page_a = page_in(context_a)
            login_and_select(page_a, "a", 0)
            page_a.goto(base + "/review.html", wait_until="domcontentloaded")
            expect(page_a.locator("#reviewHealth")).to_have_text("contexto isolado")
            expect(page_a.locator("#reviewContext")).to_contain_text("aplicação")
            expect(page_a.locator('a[href="/review.html"]')).to_be_visible()
            expect(page_a.locator("body")).not_to_contain_text("Current reading workspace")
            expect(page_a.locator("body")).not_to_contain_text("Formal screening readiness")
            expect(page_a.locator("#reviewRounds")).to_contain_text("Nenhum round desta aplicação")
            passed("generic_review_first_class_navigation_and_empty_state")

            round_name = "BROWSER_REVIEW_APP_A_PROJECT_0"
            page_a.locator("#reviewRoundName").fill(round_name)
            page_a.locator("#createReviewRound").click()
            expect(page_a.locator("#createReviewStatus")).to_contain_text(
                "Round criado e vinculado à aplicação atual"
            )
            expect(page_a.locator("#reviewRounds")).to_contain_text(round_name)
            page_a.reload(wait_until="domcontentloaded")
            expect(page_a.locator("#reviewRounds")).to_contain_text(round_name)
            passed("generic_review_round_persists_in_application")

            user_a = data["users"]["a"]
            with page_a.expect_navigation(wait_until="domcontentloaded"):
                page_a.locator("#nutevProjectSelect").select_option(user_a["projects"][1])
            page_a.goto(base + "/review.html", wait_until="domcontentloaded")
            expect(page_a.locator("#reviewHealth")).to_have_text("contexto isolado")
            expect(page_a.locator("#reviewRounds")).not_to_contain_text(round_name)
            passed("generic_review_same_tenant_project_isolation")

            context_b = new_context()
            page_b = page_in(context_b)
            login_and_select(page_b, "b", 0)
            page_b.goto(base + "/review.html", wait_until="domcontentloaded")
            expect(page_b.locator("#reviewHealth")).to_have_text("contexto isolado")
            expect(page_b.locator("#reviewRounds")).not_to_contain_text(round_name)
            passed("generic_review_cross_tenant_isolation")

            page_a.screenshot(path=str(output / "review-project-a1.png"), full_page=True)
            page_b.screenshot(path=str(output / "review-tenant-b.png"), full_page=True)
            assert not diagnostics, diagnostics
            passed("generic_review_no_javascript_page_errors")
        except Exception as exc:
            report = {
                "status": "FAIL",
                "checks": checks,
                "error": str(exc),
                "fixture_only": True,
                "production_contacted": False,
                "external_providers_contacted": False,
            }
            (output / "generic-review-browser.json").write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8"
            )
            for index, context in enumerate(contexts):
                for number, page in enumerate(context.pages):
                    try:
                        page.screenshot(
                            path=str(output / f"failure-{index}-{number}.png"), full_page=True
                        )
                    except Exception:
                        pass
            raise
        finally:
            (output / "browser-network.json").write_text(
                json.dumps(network, indent=2) + "\n", encoding="utf-8"
            )
            (output / "page-errors.json").write_text(
                json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8"
            )
            if (root / "server.log").exists():
                (output / "server.log").write_bytes((root / "server.log").read_bytes())
            for context in contexts:
                context.close()
            browser.close()

    report = {
        "status": "PASS",
        "checks": checks,
        "checks_passed": len(checks),
        "fixture_only": True,
        "production_contacted": False,
        "external_providers_contacted": False,
    }
    (output / "generic-review-browser.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("browser_e2e_artifacts/pilot/generic-review"),
    )
    args = parser.parse_args()
    print(json.dumps(run(args.output), indent=2))


if __name__ == "__main__":
    main()
