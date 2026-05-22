from __future__ import annotations

from nutev.analysis.relevance import score_record


SCORING_RULES = {
    "keyword_points": {
        "diabetes": 2,
        "medical nutrition therapy": 3,
    },
    "source_points": {"pubmed": 3},
    "workstream_points": {"busca2a": 3},
    "editorial_authority_points": {},
}


def test_busca2a_guidance_update_titles_score_above_baseline() -> None:
    baseline = score_record(
        {
            "title": "Nutrition therapy for diabetes and cardiometabolic risk",
            "abstract": "Medical nutrition therapy in adults with diabetes.",
            "source": "pubmed",
        },
        SCORING_RULES,
        "busca2a",
    )["relevance_score"]

    enriched = score_record(
        {
            "title": (
                "Clinical Practice Update and Best Practice Advice for "
                "nutrition therapy in diabetes"
            ),
            "abstract": "Medical nutrition therapy in adults with diabetes.",
            "source": "pubmed",
        },
        SCORING_RULES,
        "busca2a",
    )["relevance_score"]

    assert enriched > baseline


def test_busca2a_guideline_update_and_consensus_guidance_are_rewarded() -> None:
    record = score_record(
        {
            "title": (
                "Guideline Update and Consensus Guidance for medical "
                "nutrition therapy in MASLD"
            ),
            "abstract": "Adults with MASLD and cardiometabolic risk.",
            "source": "pubmed",
        },
        SCORING_RULES,
        "busca2a",
    )

    assert record["relevance_score"] >= 30
