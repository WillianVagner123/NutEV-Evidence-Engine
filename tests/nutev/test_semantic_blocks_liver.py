from nutev.querypacks.semantic_blocks import prioritized_semantic_blocks, semantic_terms


def test_busca2_liver_block_is_prioritized_for_cardiometabolic_workstreams():
    busca2a_blocks = prioritized_semantic_blocks("busca2a")
    busca2b_blocks = prioritized_semantic_blocks("busca2b")

    assert any(
        block["name"] == "cardiometabolic_liver" and block["priority"] >= 5
        for block in busca2a_blocks
    )
    assert any(
        block["name"] == "cardiometabolic_liver" and block["priority"] >= 5
        for block in busca2b_blocks
    )


def test_busca2_liver_terms_include_long_form_mash_variants():
    busca2a_terms = semantic_terms("busca2a", min_priority=4)
    busca2b_terms = semantic_terms("busca2b", min_priority=4)

    expected_terms = {
        "metabolic dysfunction-associated steatohepatitis",
        "metabolic dysfunction associated steatohepatitis",
        "metabolic dysfunction-associated steatotic liver disease",
        "metabolic dysfunction associated steatotic liver disease",
    }

    assert expected_terms.issubset(set(busca2a_terms))
    assert expected_terms.issubset(set(busca2b_terms))


def test_busca2_liver_terms_include_hepatic_steatosis_variants():
    busca2a_terms = semantic_terms("busca2a", min_priority=4)
    busca2b_terms = semantic_terms("busca2b", min_priority=4)

    expected_terms = {
        "hepatic steatosis",
        "liver steatosis",
        "metabolic hepatic steatosis",
        "metabolic dysfunction-associated hepatic steatosis",
        "metabolic dysfunction associated hepatic steatosis",
    }

    assert expected_terms.issubset(set(busca2a_terms))
    assert expected_terms.issubset(set(busca2b_terms))
