"""No credential or PII form may fall back to a GET submission.

A form with neither ``method`` nor ``action`` submits as ``GET`` to its own URL.
When the page's JavaScript fails to load, parse or attach its ``submit`` handler,
the browser performs that native submit and every field lands in the query string
— visible in the address bar, the browser history, the server access log and the
``Referer`` header of whatever the page loads next (CWE-598).

These pages carry passwords, one-time invitation tokens and personal data, so
each of their forms must declare an explicit ``method="post"``. ``novalidate``
stays: validation is handled in JavaScript, and it is not what leaks.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

import pytest

WEB_ROOT = Path(__file__).resolve().parents[1] / "apps" / "nutev-web"

_SENSITIVE_FIELD_NAMES = {
    "password",
    "password_confirmation",
    "email",
    "token",
    "display_name",
    "institution",
}


class _FormCollector(HTMLParser):
    """Collect each form's attributes together with the field names inside it."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.forms: list[tuple[dict[str, str | None], set[str], set[str]]] = []
        self._open: list[tuple[dict[str, str | None], set[str], set[str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "form":
            entry: tuple[dict[str, str | None], set[str], set[str]] = (attributes, set(), set())
            self._open.append(entry)
            self.forms.append(entry)
            return
        if tag == "input" and self._open:
            _, names, types = self._open[-1]
            name = str(attributes.get("name") or "").strip().casefold()
            if name:
                names.add(name)
            field_type = str(attributes.get("type") or "").strip().casefold()
            if field_type:
                types.add(field_type)

    def handle_endtag(self, tag: str) -> None:
        if tag == "form" and self._open:
            self._open.pop()


def _sensitive_forms() -> list[tuple[str, str, dict[str, str | None]]]:
    found: list[tuple[str, str, dict[str, str | None]]] = []
    for page in sorted(WEB_ROOT.glob("*.html")):
        parser = _FormCollector()
        parser.feed(page.read_text(encoding="utf-8"))
        for attributes, names, types in parser.forms:
            if "password" in types or (names & _SENSITIVE_FIELD_NAMES):
                form_id = str(attributes.get("id") or "<unnamed>")
                found.append((page.name, form_id, attributes))
    return found


def test_the_scan_actually_finds_the_known_authentication_forms() -> None:
    """Guard the guard: a broken collector would make every assertion below vacuous."""

    located = {(page, form_id) for page, form_id, _ in _sensitive_forms()}
    for expected in (
        ("login.html", "loginForm"),
        ("set-password.html", "setPasswordForm"),
        ("access-request.html", "accessRequestForm"),
    ):
        assert expected in located, f"{expected} not detected; the form scan is broken"


@pytest.mark.parametrize(
    ("page", "form_id", "attributes"),
    [pytest.param(*item, id=f"{item[0]}::{item[1]}") for item in _sensitive_forms()],
)
def test_sensitive_form_cannot_submit_via_get(
    page: str,
    form_id: str,
    attributes: dict[str, str | None],
) -> None:
    method = str(attributes.get("method") or "").strip().casefold()
    assert method == "post", (
        f"{page} form #{form_id} would submit as GET without JavaScript, "
        "placing credentials or personal data in the URL"
    )

    action = str(attributes.get("action") or "").strip()
    assert action.startswith("/api/"), (
        f"{page} form #{form_id} must post to an explicit same-origin API endpoint"
    )
