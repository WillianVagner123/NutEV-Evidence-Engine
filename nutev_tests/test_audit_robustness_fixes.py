from __future__ import annotations

import pandas as pd

from nutev.audit.claim_evaluator import detect_conflicts
from nutev.audit.claim_extractor import extract_candidate_claims_from_record
from nutev.audit.models import EvidenceClaim
from nutev.review.human_review import merge_human_review_decisions
from nutev.search.openalex import _reconstruct_abstract


def _claim(cid: str, text: str, domains: tuple[str, ...] = ("diet_quality",)) -> EvidenceClaim:
    return EvidenceClaim(
        claim_id=cid,
        document_id=f"doc_{cid}",
        claim_text=text,
        nutev_domains=list(domains),
    )


def test_detect_conflicts_ignores_substring_false_positives() -> None:
    claims = [
        _claim("a", "This study highlights fiber intake benefits."),
        _claim("b", "Participants fell below the target intake."),
    ]
    assert detect_conflicts(claims) == []


def test_detect_conflicts_flags_real_high_low_conflict() -> None:
    claims = [
        _claim("a", "Guidelines recommend a high sodium intake."),
        _claim("b", "Guidelines recommend a low sodium intake."),
    ]
    conflicts = detect_conflicts(claims)
    assert len(conflicts) == 1
    assert conflicts[0]["type"] == "possible_conflict"


def test_extract_claims_dedupes_repeated_sentences() -> None:
    sentence = "Guidelines recommend increasing vegetable intake for obesity."
    record = {"document_id": "doc_1", "abstract": sentence, "extracted_text": sentence}
    claims = extract_candidate_claims_from_record(record, {}, {})
    ids = [c.claim_id for c in claims]
    assert ids, "expected at least one claim"
    assert len(ids) == len(set(ids))


def test_reconstruct_abstract_orders_words_by_position() -> None:
    inverted = {"world": [1], "hello": [0], "again": [2]}
    assert _reconstruct_abstract(inverted) == "hello world again"
    assert _reconstruct_abstract(None) == ""
    assert _reconstruct_abstract({}) == ""


def test_merge_human_review_decisions_picks_latest_by_timestamp() -> None:
    queue = pd.DataFrame([{"item_id": "i1", "claim_text": "x"}])
    decisions = pd.DataFrame(
        [
            {"item_id": "i1", "final_decision": "old", "created_at": "2026-01-01T00:00:00+00:00"},
            {"item_id": "i1", "final_decision": "new", "created_at": "2026-06-01T00:00:00+00:00"},
        ]
    )
    merged = merge_human_review_decisions(queue, decisions)
    assert merged.iloc[0]["final_decision"] == "new"
