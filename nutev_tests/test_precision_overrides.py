from __future__ import annotations

from nutev.analysis.relevance import keep_candidate_for_download, score_record


EMPTY_SCORING_RULES = {
    "keyword_points": {},
    "source_points": {},
    "workstream_points": {},
    "editorial_authority_points": {},
}


def test_bariatric_surgery_noise_is_hard_excluded_from_download_candidates() -> None:
    record = score_record(
        {
            "title": "Randomized trial of metabolic surgery for obesity and type 2 diabetes",
            "source": "pubmed",
        },
        EMPTY_SCORING_RULES,
        "busca2b",
    )

    assert "bariatric_or_metabolic_surgery" in record["out_of_scope_flags"]
    assert record["out_of_scope_penalty"] <= -10
    assert not keep_candidate_for_download(record, "busca2b")


def test_nutrition_guideline_candidates_are_not_blocked_by_precision_override() -> None:
    record = score_record(
        {
            "title": "Clinical practice guideline for medical nutrition therapy in obesity and type 2 diabetes",
            "source": "pubmed",
        },
        EMPTY_SCORING_RULES,
        "busca2a",
    )

    assert "bariatric_or_metabolic_surgery" not in record["out_of_scope_flags"]
    assert keep_candidate_for_download(record, "busca2a")
