from nutev.querypacks.ckm_extensions import apply_ckm_extensions
from nutev.querypacks.semantic_blocks import semantic_terms


def test_ckm_renal_metabolic_terms_extend_cardiometabolic_workstreams() -> None:
    apply_ckm_extensions()

    terms = {term.lower() for term in semantic_terms("busca2a")}

    assert "cardiovascular-kidney-metabolic syndrome" in terms
    assert "chronic kidney disease" in terms
    assert "albuminuria" in terms


def test_ckm_extension_is_idempotent() -> None:
    apply_ckm_extensions()
    before = semantic_terms("busca2b").count("chronic kidney disease")

    apply_ckm_extensions()
    after = semantic_terms("busca2b").count("chronic kidney disease")

    assert before == 1
    assert after == 1
