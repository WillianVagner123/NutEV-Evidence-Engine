from __future__ import annotations

from pathlib import Path
import sys

WEB = Path(__file__).resolve().parents[1] / "apps" / "nutev-web"
sys.path.insert(0, str(WEB))

from request_boundary import pilot_route_kind  # noqa: E402


def test_generic_review_is_private_tenant_api_not_public_or_legacy_blocked() -> None:
    assert pilot_route_kind("/api/review") == "private_api"
    assert pilot_route_kind("/api/review/rounds/rnd_fixture") == "private_api"
    assert pilot_route_kind("/api/review/decision") == "private_api"
    assert pilot_route_kind("/api/review/submit") == "private_api"


def test_unknown_neighboring_api_remains_fail_closed() -> None:
    assert pilot_route_kind("/api/reviewer-legacy") == "blocked"
    assert pilot_route_kind("/api/review-legacy") == "blocked"
