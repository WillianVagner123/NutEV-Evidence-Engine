"""Silent-swallow → logged loss (T2): official-source failures must leave a trace.

Control flow is unchanged (a bad source/manifest is still skipped), but the drop
is now logged, so silent shrinkage of the official corpus becomes auditable.
"""
from __future__ import annotations

import logging
from pathlib import Path

from nutev.search.official_sources import load_official_manifest, manifest_sources


def test_malformed_source_is_logged_and_good_rows_kept(caplog):
    manifest = {
        "workstreams": {
            "busca1": [
                {"name": "WHO", "url": "https://who.int/guideline"},
                "this is not a dict — would raise on .get",
            ]
        }
    }
    with caplog.at_level(logging.WARNING, logger="nutev.search.official_sources"):
        rows = manifest_sources(manifest, "busca1")

    # The valid source survives; the malformed one is dropped but recorded.
    assert [r["title"] for r in rows] == ["WHO"]
    assert any("official source row dropped" in rec.message for rec in caplog.records)


def test_unreadable_manifest_is_logged(tmp_path: Path, caplog):
    (tmp_path / "official_sources_manifest.json").write_text("{ not valid json ]", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="nutev.search.official_sources"):
        manifest = load_official_manifest(tmp_path, include_countries=False)

    assert manifest == {}
    assert any("official manifest unreadable" in rec.message for rec in caplog.records)


def test_missing_manifest_is_not_logged_as_error(tmp_path: Path, caplog):
    # A simply-absent file is normal, not a corruption — it must NOT warn.
    with caplog.at_level(logging.WARNING, logger="nutev.search.official_sources"):
        manifest = load_official_manifest(tmp_path, include_countries=False)

    assert manifest == {}
    assert not any("unreadable" in rec.message for rec in caplog.records)
