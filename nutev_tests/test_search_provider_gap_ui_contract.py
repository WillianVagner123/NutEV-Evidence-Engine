from pathlib import Path


WEB_ROOT = Path("apps/nutev-web")


def test_provider_gap_statuses_are_human_readable_and_counted_once() -> None:
    app = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

    assert "partial:'parcial'" in app
    assert "status==='partial'?'partial'" in app
    assert "function providerGapCount(data)" in app

    for field in (
        "failed_providers",
        "unavailable_providers",
        "partial_providers",
        "skipped_providers",
        "non_exhaustive_providers",
    ):
        assert field in app

    assert "const providers=new Set()" in app
    assert "const providerGaps=providerGapCount(data)" in app


def test_partial_provider_badge_is_visually_a_warning() -> None:
    css = (WEB_ROOT / "search-ux.css").read_text(encoding="utf-8")

    assert ".provider-badge.partial" in css
    assert "#fff9ec" in css
    assert "#6f5717" in css
