from nutev.querypacks import semantic_blocks
from nutev.querypacks.food_access_extensions import apply_food_access_benefit_extensions


def _lower_values(block_name: str, field: str) -> set[str]:
    return {value.lower() for value in semantic_blocks.SEMANTIC_RESEARCH_BLOCKS[block_name][field]}


def test_food_access_benefit_terms_extend_all_relevant_semantic_blocks() -> None:
    apply_food_access_benefit_extensions()

    for block_name in ("equity_access", "food_prescription_programs", "implementation_science"):
        terms = _lower_values(block_name, "terms")
        document_terms = _lower_values(block_name, "document_terms")

        assert "medically tailored meal program" in terms
        assert "food as medicine cardiometabolic" in terms
        assert "grocery prescription diabetes" in terms
        assert "medically tailored meal systematic review" in document_terms
        assert "food as medicine systematic review" in document_terms


def test_food_access_benefit_extension_is_idempotent() -> None:
    apply_food_access_benefit_extensions()
    apply_food_access_benefit_extensions()

    for block_name in ("equity_access", "food_prescription_programs", "implementation_science"):
        for field in ("terms", "document_terms"):
            values = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS[block_name][field]
            normalized = [value.lower() for value in values]
            assert len(normalized) == len(set(normalized))
