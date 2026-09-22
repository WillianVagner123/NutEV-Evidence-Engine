"""Two-actor browser regression: doctorate owner and academic supervisor.

Actor A (owner) logs in, selects the workspace and the Article 1 project, reads the gate
state, administers members and logs out. Actor B (a supervisor fixture, never a real
person) logs in, reaches the same project, reads what the role is meant to read, and finds
no administrative or scientific action rendered.

Hidden buttons are not a security claim, so the run finishes by calling the forbidden
endpoints directly from the supervisor's own authenticated browser session and asserting
the server refuses them. Cross-tenant probes use a real foreign workspace and project.

Fixture only. No production path, no external provider, no scientific state.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from tools.doctorate_supervisor_fixture import doctorate_server

# Actions the supervisor must never be offered on the project hub.
_FORBIDDEN_UI_TEXT = (
    "Buscar evidências",
    "Gerenciar membros",
    "Configurar aplicação",
)

# Endpoints the supervisor must be refused even with a valid session cookie.
_FORBIDDEN_REQUESTS = (
    ("GET", "/api/workspace/members", None),
    ("POST", "/api/workspace/members", {"email": "externo@example.invalid", "role": "WORKSPACE_ADMIN"}),
    ("POST", "/api/workspace/members/status", {"user_id": "", "status": "removed"}),
    ("POST", "/api/application", {"template_id": "INTEGRATIVE_REVIEW", "configuration": {}}),
)


def _login(page, base: str, actor: dict) -> None:
    page.goto(base + "/login.html", wait_until="domcontentloaded")
    expect(page.locator("#loginForm")).to_be_visible()
    page.locator("#loginEmail").fill(actor["email"])
    page.locator("#loginPassword").fill(actor["password"])
    page.locator("#loginSubmit").click()
    page.wait_for_url(base + "/", timeout=15_000)


def _select_context(page, actor: dict) -> None:
    expect(page.locator("#nutevWorkspaceSelect")).to_be_visible()
    with page.expect_navigation(wait_until="domcontentloaded"):
        page.locator("#nutevWorkspaceSelect").select_option(actor["workspace_id"])
    expect(page.locator("#nutevProjectSelect")).to_be_enabled()
    with page.expect_navigation(wait_until="domcontentloaded"):
        page.locator("#nutevProjectSelect").select_option(actor["project_id"])
    expect(page.locator("#nutevProjectSelect")).to_have_value(actor["project_id"])


def _logout(page, base: str) -> None:
    page.locator("#nutevLogoutButton").click()
    page.wait_for_url("**/login.html", timeout=15_000)


def _api(page, base: str, method: str, path: str, payload=None) -> dict:
    """Call an endpoint from inside the page, so the real session cookie is used."""
    return page.evaluate(
        """async ({base, method, path, payload}) => {
            const options = {method, credentials: 'same-origin', cache: 'no-store'};
            if (payload !== null) {
                options.headers = {'Content-Type': 'application/json'};
                options.body = JSON.stringify(payload);
            }
            const response = await fetch(base + path, options);
            let body = {};
            try { body = await response.json(); } catch (error) { body = {}; }
            return {status: response.status, body};
        }""",
        {"base": base, "method": method, "path": path, "payload": payload},
    )


def _expect_gate_panel(page) -> dict:
    """The gate panel must render the canonical closed state, with no gate shown as open."""
    expect(page.locator("#scientificStatePanel")).to_be_visible()
    grid = page.locator("#gateGrid")
    expect(grid).to_contain_text("Discovery")
    expect(grid).to_contain_text("PRESS")
    expect(grid).to_contain_text("GF-10")
    expect(grid).to_contain_text("Busca formal")
    expect(grid).to_contain_text("PRISMA formal")
    expect(grid).to_contain_text("Pendente")
    expect(grid).to_contain_text("Não autorizado")
    expect(grid).to_contain_text("Não executada")
    expect(grid).to_contain_text("Não criado")
    assert page.locator("#gateGrid .gate-card.is-open").count() == 0, "no Article 1 gate may render as open"
    return {"open_gates": 0}


def _run_owner(page, base: str, data: dict, checks: list) -> None:
    owner = data["owner"]
    _login(page, base, owner)
    _select_context(page, owner)
    checks.append({"check": "owner_logs_in_and_selects_workspace_and_project", "status": "PASS"})

    page.goto(base + "/project.html", wait_until="domcontentloaded")
    expect(page.locator("#projectState")).to_contain_text("Artigo 1 (fixture)")
    expect(page.locator("#applicationPanel")).to_contain_text("Revisão de escopo")
    checks.append({"check": "owner_sees_article1_project_and_application", "status": "PASS"})

    _expect_gate_panel(page)
    checks.append({"check": "owner_sees_canonical_closed_gate_state", "status": "PASS"})

    expect(page.locator("#adminSection")).to_be_visible()
    expect(page.locator("#projectModules")).to_contain_text("Buscar evidências")
    checks.append({"check": "owner_is_offered_member_administration_and_search", "status": "PASS"})

    page.goto(base + "/members.html", wait_until="domcontentloaded")
    expect(page.locator("#rosterPanel")).to_be_visible()
    expect(page.locator("#roster")).to_contain_text("Professor orientador")
    expect(page.locator("#roster")).to_contain_text("Proprietário do workspace")
    # The owner's own row offers no status controls, so ownership cannot be dropped by hand.
    owner_row = page.locator(f'.member-row[data-member="{owner["user_id"]}"]')
    assert owner_row.locator("button[data-action]").count() == 0
    # WORKSPACE_OWNER is never an assignable option.
    assert page.locator('#grantRole option[value="WORKSPACE_OWNER"]').count() == 0
    checks.append({"check": "owner_manages_members_without_ownership_transfer", "status": "PASS"})

    _logout(page, base)
    checks.append({"check": "owner_logs_out", "status": "PASS"})


def _run_supervisor(page, base: str, data: dict, checks: list) -> None:
    supervisor = data["supervisor"]
    outsider = data["outsider"]
    _login(page, base, supervisor)
    _select_context(page, supervisor)
    checks.append({"check": "supervisor_logs_in_and_reaches_authorized_workspace", "status": "PASS"})

    # Only the authorized workspace is offered at all.
    options = page.locator("#nutevWorkspaceSelect option")
    values = {options.nth(index).get_attribute("value") for index in range(options.count())}
    assert outsider["workspace_id"] not in values, "a foreign workspace must not be listed"
    checks.append({"check": "supervisor_sees_only_authorized_workspaces", "status": "PASS"})

    page.goto(base + "/project.html", wait_until="domcontentloaded")
    expect(page.locator("#projectState")).to_contain_text("Artigo 1 (fixture)")
    expect(page.locator("#projectState")).to_contain_text("Professor orientador")
    expect(page.locator("#applicationPanel")).to_contain_text("Revisão de escopo")
    checks.append({"check": "supervisor_reads_project_and_application", "status": "PASS"})

    _expect_gate_panel(page)
    checks.append({"check": "supervisor_reads_canonical_closed_gate_state", "status": "PASS"})

    expect(page.locator("#projectModules")).to_contain_text("Biblioteca")
    expect(page.locator("#projectModules")).to_contain_text("Histórico de buscas")
    expect(page.locator("#projectModules")).to_contain_text("Revisão humana (leitura)")
    checks.append({"check": "supervisor_is_offered_the_reads_of_the_role", "status": "PASS"})

    # Forbidden actions are not presented, rather than presented and refused on click. This
    # asserts on what the supervisor can actually see, so a control left in the DOM but hidden
    # still counts as not offered; the endpoint probes below are what prove the boundary.
    for label in _FORBIDDEN_UI_TEXT:
        visible = page.locator(f':text("{label}")').filter(visible=True).count()
        assert visible == 0, f"supervisor was offered a forbidden action: {label}"
    expect(page.locator("#adminSection")).to_be_hidden()
    expect(page.locator("#templatePanel")).to_be_hidden()
    expect(page.locator('.sidebar nav a[href="/search.html"]')).to_have_count(0)
    checks.append({"check": "supervisor_is_never_offered_a_forbidden_action", "status": "PASS"})

    # The members screen itself stays closed if reached directly by URL.
    page.goto(base + "/members.html", wait_until="domcontentloaded")
    expect(page.locator("#membersState")).to_contain_text("Você não gerencia os membros deste workspace")
    expect(page.locator("#grantPanel")).to_be_hidden()
    expect(page.locator("#rosterPanel")).to_be_hidden()
    checks.append({"check": "supervisor_reaching_members_url_directly_is_refused", "status": "PASS"})

    # Hidden buttons prove nothing: call the endpoints with the real session.
    page.goto(base + "/project.html", wait_until="domcontentloaded")
    refusals = []
    for method, path, payload in _FORBIDDEN_REQUESTS:
        result = _api(page, base, method, path, payload)
        assert result["status"] in {400, 403, 404, 409}, (method, path, result)
        assert result["status"] != 200, (method, path, result)
        refusals.append({"method": method, "path": path, "status": result["status"]})
    checks.append({"check": "supervisor_forbidden_endpoints_refuse_directly", "status": "PASS", "detail": refusals})

    # Reads the role does carry still succeed, so the denials above are not a blanket block.
    for path in ("/api/application", "/api/searches", "/api/article1/scientific-state"):
        result = _api(page, base, "GET", path, None)
        assert result["status"] == 200, (path, result)
    checks.append({"check": "supervisor_permitted_reads_still_succeed", "status": "PASS"})

    # Knowing a valid foreign ID must not select it.
    result = _api(
        page,
        base,
        "POST",
        "/api/context/select",
        {"workspace_id": outsider["workspace_id"], "project_id": outsider["project_id"]},
    )
    assert result["status"] != 200, result
    checks.append({"check": "supervisor_cannot_select_a_foreign_workspace", "status": "PASS"})

    _logout(page, base)
    checks.append({"check": "supervisor_logs_out", "status": "PASS"})


def run(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    checks: list[dict] = []
    diagnostics: list[str] = []

    with doctorate_server() as (base, data, _root), sync_playwright() as playwright:
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

        try:
            _run_owner(page, base, data, checks)
            _run_supervisor(page, base, data, checks)

            if diagnostics:
                raise AssertionError(diagnostics)
            checks.append({"check": "no_javascript_page_errors", "status": "PASS"})
            report = {
                "status": "PASS",
                "actors": ["workspace_owner", "academic_supervisor"],
                "checks": checks,
                "fixture_only": True,
                "production_contacted": False,
                "external_providers_contacted": False,
                "scientific_state_modified": False,
                "scientific_approval_created": False,
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
            (output / "doctorate-supervisor.json").write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8"
            )
            raise
        finally:
            context.close()
            browser.close()

    (output / "doctorate-supervisor.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("browser_e2e_artifacts/pilot/doctorate-supervisor"),
    )
    args = parser.parse_args()
    print(json.dumps(run(args.output), indent=2))


if __name__ == "__main__":
    main()
