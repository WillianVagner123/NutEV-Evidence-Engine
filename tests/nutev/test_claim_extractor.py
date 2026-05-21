from nutev.audit.claim_extractor import extract_candidate_claims_from_record


def test_extract_food_processing_claim():
    rec = {"document_id": "d1", "extracted_text": "Adults should reduce ultra-processed foods."}
    claims = extract_candidate_claims_from_record(rec, {"domains": {"food_processing": ["ultra-processed"]}}, {})
    assert claims
    assert "food_processing" in claims[0].nutev_domains
