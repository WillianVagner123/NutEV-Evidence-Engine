"""Entity registries: file_asset × document_version × document_family (§7.1, §18)."""
from __future__ import annotations

from nutev.analysis.registries import build_registries, is_aggregator


def _asset(name, country, title, year, sha, url="", kind="fulltext_pdf", lang=""):
    return {
        "name": name, "country": country, "reference_title": title,
        "document_version": str(year), "sha256": sha, "source_url": url,
        "fulltext_status": kind, "language": lang, "archived_pdf_path": f"/x/{sha}.pdf",
    }


def test_pdf_and_html_mirror_collapse_to_one_version():
    # §18.6 spirit: two assets of the SAME document/edition are one version.
    rows = [
        _asset("US DGA", "usa", "Dietary Guidelines for Americans", 2025, "aaa", kind="fulltext_pdf"),
        _asset("US DGA (web)", "usa", "Dietary Guidelines for Americans", 2025, "bbb", kind="fulltext_html"),
    ]
    reg = build_registries(rows)
    assert len(reg["file_assets"]) == 2       # two physical files
    assert len(reg["versions"]) == 1          # one version
    assert len(reg["families"]) == 1          # one family
    assert reg["versions"][0]["n_assets"] == 2


def test_editions_are_superseded_vs_current():
    # §18.5: DGA 2020 superseded when DGA 2025 exists; same family.
    rows = [
        _asset("US DGA 2020", "usa", "Dietary Guidelines for Americans", 2020, "old"),
        _asset("US DGA 2025", "usa", "Dietary Guidelines for Americans", 2025, "new"),
    ]
    reg = build_registries(rows)
    assert len(reg["families"]) == 1
    assert len(reg["versions"]) == 2
    by_year = {v["year"]: v["status"] for v in reg["versions"]}
    assert by_year[2025] == "current"
    assert by_year[2020] == "superseded"


def test_aggregator_not_counted_as_document():
    # §18.2: an aggregating spreadsheet is never one document unit.
    rows = [
        _asset("fao_fbdg_all_countries", "", "All countries", 2024, "agg", kind="fulltext_pdf"),
        _asset("Brazil FBDG", "brazil", "Guia Alimentar", 2014, "br"),
    ]
    assert is_aggregator(rows[0]) is True
    reg = build_registries(rows)
    assert len(reg["file_assets"]) == 1  # only the real document
    assert len(reg["families"]) == 1
    excl = [d for d in reg["denominators"] if d["name"] == "aggregators_excluded"][0]
    assert excl["n"] == 1


def test_denominators_are_distinct_not_summed():
    rows = [
        _asset("US DGA 2020", "usa", "Dietary Guidelines for Americans", 2020, "a"),
        _asset("US DGA 2025", "usa", "Dietary Guidelines for Americans", 2025, "b"),
        _asset("US DGA 2025 web", "usa", "Dietary Guidelines for Americans", 2025, "c", kind="fulltext_html"),
        _asset("Brazil FBDG", "brazil", "Guia Alimentar", 2014, "d"),
    ]
    reg = build_registries(rows)
    names = {d["name"]: d["n"] for d in reg["denominators"]}
    assert names["file_assets"] == 4        # 4 files
    assert names["document_versions"] == 3  # US2020, US2025 (pdf+web = 1), BR2014
    assert names["document_families"] == 2  # US DGA, Brazil FBDG


def test_empty_rows_safe():
    reg = build_registries([])
    assert reg["file_assets"] == [] and reg["families"] == []
    assert {d["name"] for d in reg["denominators"]} >= {"file_assets", "document_versions", "document_families"}
