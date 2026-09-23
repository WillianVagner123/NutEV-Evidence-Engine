"""Contracts for stable context navigation in Playwright product gates."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "tools" / "browser_context_navigation.py"
BROWSER_RUNNERS = (
    ROOT / "tools" / "run_pilot_browser_closeout.py",
    ROOT / "tools" / "run_onboarding_persistence_browser.py",
    ROOT / "tools" / "run_generic_review_browser.py",
    ROOT / "tools" / "run_doctorate_supervisor_browser.py",
)


def test_context_navigation_helper_only_tolerates_known_superseded_navigation_race() -> None:
    source = HELPER.read_text(encoding="utf-8")

    assert "net::ERR_ABORTED" in source
    assert "maybe frame was detached" in source
    assert "if not any(marker in message" in source
    assert "raise" in source
    assert 'expect(page.locator(selector)).to_have_value(value' in source


def test_context_selecting_browser_runners_use_the_stable_helper() -> None:
    for path in BROWSER_RUNNERS:
        source = path.read_text(encoding="utf-8")
        assert "from tools.browser_context_navigation import select_context_option" in source
        assert "select_context_option(" in source


def test_context_selecting_browser_runners_do_not_own_raw_navigation_waits() -> None:
    for path in BROWSER_RUNNERS:
        source = path.read_text(encoding="utf-8")
        assert "expect_navigation" not in source


def test_logout_final_state_helper_uses_dom_assertions_not_navigation_watcher() -> None:
    source = HELPER.read_text(encoding="utf-8")
    pilot = (ROOT / "tools" / "run_pilot_browser_closeout.py").read_text(encoding="utf-8")
    supervisor = (ROOT / "tools" / "run_doctorate_supervisor_browser.py").read_text(encoding="utf-8")

    assert "def expect_login_page" in source
    assert 'expect(page).to_have_url(base + "/login.html"' in source
    assert 'expect(page.locator("#loginForm")).to_be_visible' in source

    assert "from tools.browser_context_navigation import select_context_option" in pilot
    assert "from tools.browser_context_navigation import expect_login_page" in pilot
    assert "expect_login_page(tab,base)" in pilot
    assert "expect_login_page(a,base)" in pilot
    assert "tab.wait_for_url('**/login.html')" not in pilot
    assert "a.wait_for_url('**/login.html')" not in pilot

    assert "from tools.browser_context_navigation import select_context_option" in supervisor
    assert "from tools.browser_context_navigation import expect_login_page" in supervisor
    assert "expect_login_page(page, base, timeout=15_000)" in supervisor
