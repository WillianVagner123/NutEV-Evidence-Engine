"""Tests for the pilot-audit fixes:
- extraction rejects anti-bot / redirect / too-thin pages (no false positives);
- dietary-pattern detection recognizes synonyms and respects word boundaries;
- a claim is only "supported" when backed by a substantial verbatim quote from
  genuinely-extracted text.
"""
from __future__ import annotations

import logging
from pathlib import Path

from nutev.extract.smart_extract import extract_document, looks_like_junk_text
from nutev.search.normalize import infer_diet_pattern
from nutev.audit.claim_extractor import (
    extract_candidate_claims_from_record,
    MIN_SUPPORTED_QUOTE_CHARS,
)

logger = logging.getLogger("test")


def test_looks_like_junk_text_detects_blockers():
    assert looks_like_junk_text("Checking your browser before accessing. reCAPTCHA")
    assert looks_like_junk_text("Just a moment... Cloudflare")
    assert looks_like_junk_text("Redirecting")
    assert looks_like_junk_text("")
    # A real document body is not junk.
    real = "Dietary guidelines recommend increasing vegetable and fruit intake. " * 20
    assert not looks_like_junk_text(real)


def test_extract_document_flags_junk_html(tmp_path: Path):
    junk = tmp_path / "blocked.html"
    junk.write_text(
        "<html><body>Checking your browser before accessing diabetesjournals.org. "
        "Please enable JavaScript and reload. reCAPTCHA.</body></html>",
        encoding="utf-8",
    )
    result = extract_document(junk, tmp_path / "ocr", tmp_path / "out", logger)
    assert result["extraction_status"] == "junk_or_blocked"


def test_extract_document_accepts_real_html(tmp_path: Path):
    body = "Official dietary guidelines recommend reducing ultra-processed foods. " * 20
    page = tmp_path / "guide.html"
    page.write_text(f"<html><body><h1>Guide</h1><p>{body}</p></body></html>", encoding="utf-8")
    result = extract_document(page, tmp_path / "ocr", tmp_path / "out", logger)
    assert result["extraction_status"] == "ok"


def test_infer_diet_pattern_synonyms_and_boundaries():
    assert "mediterranean" in infer_diet_pattern("The MedDiet improved outcomes")
    assert "dash" in infer_diet_pattern("Dietary Approaches to Stop Hypertension (DASH)")
    assert "plant-based" in infer_diet_pattern("a pescatarian, plant-forward eating pattern")
    assert "nordic" in infer_diet_pattern("the New Nordic diet")
    assert "intermittent-fasting" in infer_diet_pattern("time-restricted eating and intermittent fasting")
    # 'dash' must not match 'dashboard'.
    assert "dash" not in infer_diet_pattern("open the analytics dashboard")


def _record(extracted_text: str) -> dict:
    return {
        "document_id": "doc1",
        "title": "",
        "abstract": "",
        "extracted_text": extracted_text,
        "url": "https://example.org/doc",
    }


def test_claim_supported_only_with_substantial_quote():
    sentence = "Clinicians should recommend increasing whole grains and vegetables for adults."
    assert len(sentence) >= MIN_SUPPORTED_QUOTE_CHARS
    extracted = f"Background context sentence. {sentence}"
    claims = extract_candidate_claims_from_record(_record(extracted), {}, {})
    assert claims, "expected at least one claim"
    supported = [c for c in claims if c.claim_status == "supported"]
    assert supported, "a substantial quote present in extracted text should be supported"
    assert supported[0].exact_quote
    assert supported[0].quote_location == "extracted_text"


def test_claim_inference_only_when_no_extracted_text():
    # Same sentence but only in the title/abstract, not in extracted_text.
    rec = {"document_id": "d", "title": "Clinicians should recommend increasing whole grains and vegetables.", "abstract": "", "extracted_text": ""}
    claims = extract_candidate_claims_from_record(rec, {}, {})
    assert claims
    assert all(c.claim_status == "inference_only" for c in claims)
    assert all(not c.exact_quote for c in claims)
