from __future__ import annotations

from nutev.querypacks import semantic_blocks


def test_food_as_medicine_referral_terms_extend_priority_blocks() -> None:
    expected_terms = {
        "food as medicine clinic",
        "produce prescription implementation",
        "medically tailored groceries intervention",
        "nutrition security intervention",
        "clinical-community food referral",
        "grocery prescription",
        "grocery prescription program",
        "food farmacy",
        "food farmacy program",
        "healthy food box",
    }
    expected_document_terms = {
        "food as medicine implementation study",
        "produce prescription program evaluation",
        "medically tailored grocery program evaluation",
        "nutrition security program evaluation",
        "grocery prescription implementation study",
        "grocery prescription program evaluation",
        "food farmacy implementation study",
        "food farmacy program evaluation",
        "healthy food box intervention trial",
    }

    for block_name in ("food_prescription_programs", "equity_access"):
        block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS[block_name]
        assert expected_terms.issubset(set(block["terms"]))
        assert expected_document_terms.issubset(set(block["document_terms"]))


def test_food_as_medicine_referral_terms_support_implementation_queries() -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["implementation_science"]

    assert "food pharmacy implementation" in block["terms"]
    assert "food pharmacy program evaluation" in block["document_terms"]
    assert "grocery prescription implementation" in block["terms"]
    assert "grocery prescription implementation study" in block["document_terms"]
    assert "food farmacy implementation" in block["terms"]
    assert "food farmacy implementation study" in block["document_terms"]
    assert len(block["terms"]) == len({term.lower() for term in block["terms"]})
