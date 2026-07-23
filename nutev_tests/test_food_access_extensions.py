from nutev.querypacks import semantic_blocks


EXPECTED_TERMS = {
    "food resource navigation",
    "healthy food navigation",
    "produce prescription referral",
    "food as medicine referral",
    "food is medicine referral",
    "medically tailored meal referral",
    "clinical-community food referral",
}

EXPECTED_DOCUMENT_TERMS = {
    "food resource navigation program evaluation",
    "healthy food navigation program evaluation",
    "produce prescription referral program evaluation",
    "food as medicine referral program evaluation",
    "medically tailored meal referral program evaluation",
    "clinical-community food referral program evaluation",
}


def test_food_access_navigation_terms_extend_core_blocks():
    for block_name in ("equity_access", "food_prescription_programs", "implementation_science"):
        block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS[block_name]
        assert EXPECTED_TERMS.issubset(set(block["terms"]))
        assert EXPECTED_DOCUMENT_TERMS.issubset(set(block["document_terms"]))
