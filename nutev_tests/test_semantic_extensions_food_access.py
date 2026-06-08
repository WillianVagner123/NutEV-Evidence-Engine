from __future__ import annotations

from nutev.querypacks import semantic_blocks


def test_food_as_medicine_referral_terms_extend_priority_blocks() -> None:
    expected_terms = {
        "food as medicine clinic",
        "produce prescription implementation",
        "medically tailored groceries intervention",
        "nutrition security intervention",
        "clinical-community food referral",
    }
    expected_document_terms = {
        "food as medicine implementation study",
        "produce prescription program evaluation",
        "medically tailored grocery program evaluation",
        "nutrition security program evaluation",
    }

    for block_name in ("food_prescription_programs", "equity_access"):
        block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS[block_name]
        assert expected_terms.issubset(set(block["terms"]))
        assert expected_document_terms.issubset(set(block["document_terms"]))


def test_food_as_medicine_referral_terms_support_implementation_queries() -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["implementation_science"]

    assert "food pharmacy implementation" in block["terms"]
    assert "food pharmacy program evaluation" in block["document_terms"]
    assert len(block["terms"]) == len({term.lower() for term in block["terms"]})
