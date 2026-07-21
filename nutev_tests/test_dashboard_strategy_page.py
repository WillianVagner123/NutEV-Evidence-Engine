"""Smoke test for the dashboard Search Strategy page (C4 surfaced in the UI).

Uses Streamlit's AppTest to render the page headlessly and assert the PICOS
inputs produce the per-provider expression grid without raising. Skips cleanly
when Streamlit (the optional `dashboard` extra) is not installed, so core-only
CI is unaffected.
"""
from __future__ import annotations

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

_DASHBOARD = "src/nutev/ui/dashboard.py"


def _strategy_app() -> AppTest:
    at = AppTest.from_file(_DASHBOARD, default_timeout=30)
    at.run()
    at.sidebar.radio[0].set_value("Search Strategy").run()
    return at


def test_strategy_page_renders_without_concepts():
    at = _strategy_app()
    assert not at.exception
    # No concepts entered yet -> the grid is not built (empty-state instead).
    assert all("tiab" not in c.value for c in at.code)


def test_strategy_page_builds_grid_from_picos_inputs():
    at = _strategy_app()
    at.text_area[0].set_value("adults\nobesity").run()   # Population block
    assert not at.exception
    codes = [c.value for c in at.code]
    # 4 providers x 3 breadths = 12 expression blocks.
    assert len(codes) == 12
    assert any("(adults[tiab] OR obesity[tiab])" in c for c in codes)
