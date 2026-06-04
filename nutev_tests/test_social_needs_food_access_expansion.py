from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


SOCIAL_NEEDS_TERMS = {
    "nutrition security intervention",
    "social needs referral",
    "community food program",
    "food bank partnership",
    "medically tailored food referral",
    "produce prescription referral",
}

SOCIAL_NEEDS_DOCUMENT_TERMS = {
    "social needs referral program",
    "community-supported food program",
    "food bank partnership",
    "medically tailored food referral",
    "produce prescription referral",
}


def test_busca2b_semantic_terms_include_social_needs_food_access_referrals() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=5)}

    assert SOCIAL_NEEDS_TERMS <= terms


def test_busca1_document_terms_include_community_food_access_programs() -> None:
    document_terms = {
        term.lower()
        for term in semantic_terms("busca1", field="document_terms", min_priority=3)
    }

    assert SOCIAL_NEEDS_DOCUMENT_TERMS <= document_terms
