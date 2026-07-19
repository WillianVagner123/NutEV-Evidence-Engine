"""Typed error hierarchy + lost-coverage recorder (audit §3)."""
from __future__ import annotations

from pathlib import Path

from nutev.errors import (
    ArtifactContractError,
    DocumentExtractionError,
    NutEVError,
    OCRRequiredError,
    ProviderRateLimitError,
    ProviderUnavailableError,
)
from nutev.telemetry.coverage import CoverageLog, write_coverage_report


def test_error_codes_are_stable_and_typed():
    assert ProviderUnavailableError().code == "provider_unavailable"
    assert ProviderRateLimitError().code == "provider_rate_limit"
    assert ArtifactContractError().code == "artifact_contract_error"
    # OCRRequiredError is a DocumentExtractionError is a NutEVError.
    assert issubclass(OCRRequiredError, DocumentExtractionError)
    assert issubclass(DocumentExtractionError, NutEVError)


def test_error_carries_context():
    err = ProviderUnavailableError("boom", provider="pubmed", query="diet", stage="search",
                                   recoverable=True, attempt=2, fallback_used="europepmc",
                                   coverage_impact="pubmed hits missing")
    d = err.to_dict()
    assert d["code"] == "provider_unavailable" and d["provider"] == "pubmed"
    assert d["attempt"] == 2 and d["fallback_used"] == "europepmc"
    assert d["coverage_impact"] == "pubmed hits missing"


def test_coverage_log_records_generic_and_typed():
    log = CoverageLog()
    log.record_exception(ValueError("bad"), code="artifact_contract_error",
                         component="thematic", stage="enrichment", impact="no theme cols")
    log.record_error(ProviderRateLimitError("429", provider="crossref"), component="search")
    s = log.summary()
    assert s["total_events"] == 2
    assert s["by_code"]["artifact_contract_error"] == 1
    assert s["by_code"]["provider_rate_limit"] == 1
    assert "thematic" in s["by_component"] and "search" in s["by_component"]


def test_coverage_report_written(tmp_path: Path):
    log = CoverageLog()
    log.record(code="ocr_required", component="extraction", stage="ocr",
               reason="tesseract missing", recoverable=False, impact="1 doc unread")
    summary = write_coverage_report(log, tmp_path)
    assert summary["unrecoverable"] == 1
    assert (tmp_path / "coverage_loss.csv").exists()
    assert (tmp_path / "coverage_loss.json").exists()


def test_clean_run_has_empty_coverage(tmp_path: Path):
    log = CoverageLog()
    assert log.is_empty()
    summary = write_coverage_report(log, tmp_path)
    assert summary["total_events"] == 0   # nothing lost -> zeroed report, not hidden
