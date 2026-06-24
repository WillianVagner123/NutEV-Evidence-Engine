from nutev.querypacks.dietary_adherence_terms import (
    DIETARY_ADHERENCE_DOCUMENT_TERMS,
    DIETARY_ADHERENCE_SCORE_BONUSES,
    DIETARY_ADHERENCE_SCORE_TERMS,
)


def test_dietary_adherence_terms_are_nutrition_anchored() -> None:
    all_terms = [
        *DIETARY_ADHERENCE_SCORE_TERMS,
        *DIETARY_ADHERENCE_DOCUMENT_TERMS,
        *(term for term, _ in DIETARY_ADHERENCE_SCORE_BONUSES),
    ]

    assert all_terms
    assert "score" not in all_terms
    assert "index" not in all_terms
    assert "adherence score" not in all_terms
    assert any("mediterranean diet adherence score" == term for term in all_terms)

    anchors = ("diet", "dietary", "eating", "mediterranean", "dash", "plant-based")
    assert all(any(anchor in term for anchor in anchors) for term in all_terms)


def test_dietary_adherence_bonus_weights_are_moderate() -> None:
    assert DIETARY_ADHERENCE_SCORE_BONUSES
    assert all(0 < weight <= 18 for _, weight in DIETARY_ADHERENCE_SCORE_BONUSES)
