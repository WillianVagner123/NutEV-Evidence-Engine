"""Stable browser helpers for context selects that intentionally reload the page.

The NutEV shell persists a workspace/project selection through /api/context/select and then
reloads. Chromium/Playwright can report the superseded navigation as net::ERR_ABORTED or a
detached frame even when the server-side context was committed and the replacement page loaded.
These helpers tolerate only that known navigation race and still assert the final selected value,
so a failed or non-persisted context change remains a test failure.
"""
from __future__ import annotations

from playwright.sync_api import Error, expect


_KNOWN_SUPERSEDED_NAVIGATION = (
    "net::ERR_ABORTED",
    "maybe frame was detached",
)


def select_context_option(page, selector: str, value: str, *, timeout: int = 10_000) -> None:
    """Select a context value and verify the replacement page reflects it.

    Only Playwright's known superseded-navigation race is tolerated. Any other navigation error
    is re-raised, and the final DOM assertion is always required.
    """
    try:
        with page.expect_navigation(wait_until="domcontentloaded", timeout=timeout):
            page.locator(selector).select_option(value)
    except Error as exc:
        message = str(exc)
        if not any(marker in message for marker in _KNOWN_SUPERSEDED_NAVIGATION):
            raise
        # The old document may have been detached while the replacement document won the race.
        # Waiting here binds subsequent assertions to the active document.
        page.wait_for_load_state("domcontentloaded", timeout=timeout)

    expect(page.locator(selector)).to_have_value(value, timeout=timeout)
