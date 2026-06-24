from __future__ import annotations

import pytest

from nutev.querypacks.coverage_guardrails import (
    CoverageGap,
    assert_adherence_precision_coverage,
    missing_required_terms,
    normalize_term,
)


def test_normalize_term_handles_case_spacing_and_hyphens() -> None:
    assert normalize_term(" Long-Term   Adherence ") == "long term adherence"


def test_missing_required_terms_accepts_hyphen_variants() -> None:
    observed = ["long-term adherence", "dietary adherence"]
    missing = missing_required_terms(
        observed,
        required_terms=["long term adherence", "dietary adherence"],
    )

    assert missing == []


def test_assert_adherence_precision_coverage_reports_missing_terms() -> None:
    taxonomy = {
        "global": {
            "implementation_behavior": {
                "adherence": [
                    "dietary adherence",
                    "treatment adherence",
                ]
            }
        }
    }

    with pytest.raises(CoverageGap) as exc:
        assert_adherence_precision_coverage(taxonomy)

    assert "diet adherence" in str(exc.value)


def test_assert_adherence_precision_coverage_accepts_complete_block() -> None:
    taxonomy = {
        "global": {
            "implementation_behavior": {
                "adherence": [
                    "dietary adherence",
                    "diet adherence",
                    "treatment adherence",
                    "long-term adherence",
                    "long term adherence",
                    "dietary compliance",
                    "diet compliance",
                    "persistence",
                    "engagement",
                    "retention",
                    "attrition",
                    "dropout",
                    "weight maintenance",
                    "dietary maintenance",
                    "behavioral maintenance",
                    "behavioural maintenance",
                    "relapse prevention",
                    "dietary self-monitoring",
                    "self-management support",
                ]
            }
        }
    }

    assert_adherence_precision_coverage(taxonomy)
