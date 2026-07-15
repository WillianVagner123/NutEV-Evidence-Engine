"""P6 — tests for the fulltext_coverage run_summary block (offline)."""
from __future__ import annotations

from pathlib import Path

from nutev.acquire.recoverability import (
    diagnose_recoverability,
    fulltext_coverage,
    fulltext_coverage_block,
    write_recoverability_outputs,
)

_ROWS = [
    # busca1: full text extracted.
    {"workstream": "busca1", "extraction_status": "ok", "doi": "10.1/g", "pmcid": "PMC1"},
    # busca1: OCR'd full text.
    {"workstream": "busca1", "extraction_status": "ok_ocr", "doi": "10.1/h", "pmcid": ""},
    # busca2a: blocked -> metadata only.
    {"workstream": "busca2a", "extraction_status": "junk_or_blocked", "doi": "10.2/a", "pmcid": ""},
    # busca2a: never extracted -> metadata only.
    {"workstream": "busca2a", "extraction_status": "missing", "doi": "10.3/b", "pmcid": ""},
]


def test_coverage_counts_per_workstream():
    cov = fulltext_coverage(_ROWS)
    assert cov["total"] == 4
    assert cov["fulltext_extracted"] == 2
    assert cov["metadata_only"] == 2
    assert cov["pct_fulltext"] == 50.0
    assert cov["per_workstream"]["busca1"]["fulltext_extracted"] == 2
    assert cov["per_workstream"]["busca1"]["pct_fulltext"] == 100.0
    assert cov["per_workstream"]["busca2a"]["metadata_only"] == 2
    assert cov["per_workstream"]["busca2a"]["pct_fulltext"] == 0.0


def test_coverage_block_merges_recoverability_ceiling():
    recover = diagnose_recoverability(_ROWS)
    block = fulltext_coverage_block(_ROWS, recoverability=recover)["fulltext_coverage"]
    assert block["fulltext_extracted"] == 2
    assert "recoverable_ceiling" in block
    ceiling = block["recoverable_ceiling"]
    assert "overall_pct_open_access" in ceiling
    assert "busca1" in ceiling["per_workstream_pct_open_access"]


def test_coverage_block_without_recoverability_omits_ceiling():
    block = fulltext_coverage_block(_ROWS)["fulltext_coverage"]
    assert "recoverable_ceiling" not in block


def test_empty_rows_are_safe():
    cov = fulltext_coverage([])
    assert cov["total"] == 0 and cov["fulltext_extracted"] == 0
    assert cov["per_workstream"] == {}


def test_write_recoverability_outputs_writes_both(tmp_path: Path):
    recover = diagnose_recoverability(_ROWS)
    json_path = write_recoverability_outputs(recover, tmp_path)
    assert json_path.exists() and json_path.name == "fulltext_recoverability.json"
    assert (tmp_path / "fulltext_recoverability.csv").exists()
