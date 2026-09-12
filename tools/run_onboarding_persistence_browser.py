"""Browser regression for first-project application persistence.

Uses only the temporary offline pilot fixture. Never contacts production or external
providers. The purpose is to prove that an application configured through the real
UI survives refresh and a complete logout/login cycle.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from tools.pilot_closeout_fixture import pilot_server


def _login(page, base: str, user: dict) -> None:
    page.goto(base + "/login.html", wait_until="domcontentloaded")
    expect(page.locator("#loginForm")).to_be_visible()
    page.locator("#loginEmail").fill(user["email"])
    page.locator("#loginPassword").fill(user["password"])
    page.locator("#loginSubmit").click()
    page.wait_for_url(base + "/", timeout=10_000)


def _select_context(page, user: dict) -> None:
    expect(page.locator("#nutevWorkspaceSelect")).to_be_visible()
    with page.expect_navigation(wait_until="domcontentloaded"):
        page.locator("#nutevWorkspaceSelect").select_option(user["workspace_id"])
    expect(page.locator("#nutevWorkspaceSelect")).to_have_value(user["workspace_id"])
    expect(page.locator("#nutevProjectSelect")).to_be_enabled()
    with page.expect_navigation(wait_until="domcontentloaded"):
        page.locator("#nutevProjectSelect").select_option(user["projects"][0])
    expect(page.locator("#nutevProjectSelect")).to_have_value(user["projects"][0])


def _expect_configured_project(page) -> None:
    expect(page.locator("#projectHealth")).to_have_text("contexto configurado")
    expect(page.locator("#projectModules")).to_contain_text("Buscar evidências")
    expect(page.locator("#projectModules")).to_contain_text("Biblioteca")
    expect(page.locator("#projectModules")).to_contain_text("Exportações")


def run(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, str]] = []
    diagnostics: list[str] = []

    with pilot_server() as (base, data, _root), sync_playwright() as playwright:
        executable = os.environ.get("NUTEV_CHROMIUM_EXECUTABLE")
        browser = playwright.chromium.launch(
            **({"executable_path": executable} if executable else {}),
            args=["--no-sandbox"],
        )
        context = browser.new_context(viewport={"width": 1366, "height": 900})
        context.route(
            "**/*",
            lambda route: route.continue_() if route.request.url.startswith(base) else route.abort(),
        )
        page = context.new_page()
        page.on("pageerror", lambda error: diagnostics.append(str(error)))
        user = data["users"]["onboarding"]

        try:
            _login(page, base, user)
            _select_context(page, user)
            page.goto(base + "/project.html", wait_until="domcontentloaded")

            expect(page.locator("#templatePanel")).to_be_visible()
            expect(page.locator("#templatePanel")).to_contain_text(
                "Escolha como este projeto vai usar o NutEV"
            )
            page.locator(
                'input[name="applicationTemplate"][value="GENERIC_EVIDENCE_PROJECT"]'
            ).check()
            page.locator("#configureApplication").click()
            page.wait_for_load_state("domcontentloaded")
            _expect_configured_project(page)
            checks.append({"check": "configure_application_through_real_ui", "status": "PASS"})

            page.reload(wait_until="domcontentloaded")
            _expect_configured_project(page)
            checks.append({"check": "application_persists_after_refresh", "status": "PASS"})

            page.locator("#nutevLogoutButton").click()
            page.wait_for_url("**/login.html", timeout=10_000)
            _login(page, base, user)
            _select_context(page, user)
            page.goto(base + "/project.html", wait_until="domcontentloaded")
            _expect_configured_project(page)
            checks.append({"check": "application_persists_after_logout_login", "status": "PASS"})

            if diagnostics:
                raise AssertionError(diagnostics)
            checks.append({"check": "no_javascript_page_errors", "status": "PASS"})
            report = {
                "status": "PASS",
                "checks": checks,
                "fixture_only": True,
                "production_contacted": False,
                "external_providers_contacted": False,
            }
        except Exception as exc:
            try:
                page.screenshot(path=str(output / "failure.png"), full_page=True)
            except Exception:
                pass
            report = {
                "status": "FAIL",
                "checks": checks,
                "error": str(exc),
                "page_errors": diagnostics,
                "fixture_only": True,
                "production_contacted": False,
                "external_providers_contacted": False,
            }
            (output / "onboarding-persistence.json").write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8"
            )
            raise
        finally:
            context.close()
            browser.close()

    (output / "onboarding-persistence.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("browser_e2e_artifacts/pilot-onboarding-persistence"),
    )
    args = parser.parse_args()
    print(json.dumps(run(args.output), indent=2))


if __name__ == "__main__":
    main()
