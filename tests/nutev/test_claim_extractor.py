from nutev.audit.claim_extractor import extract_candidate_claims_from_record


def test_extract_claim_quote_locations_and_dedup():
    rec = {
        'document_id':'d1',
        'title':'Adults should reduce ultra-processed foods.',
        'abstract':'Adults should reduce ultra-processed foods.',
        'extracted_text':'Adults should reduce ultra-processed foods. Adults should reduce sodium.',
        'source_type':'official_guideline'
    }
    claims = extract_candidate_claims_from_record(rec, {'domains': {'food_processing':['ultra-processed'], 'policy':['sodium']}}, {})
    by_text = {c.claim_text: c for c in claims}
    assert any(c.quote_location == 'title' for c in claims)
    assert any(c.quote_location == 'extracted_text' for c in claims)
    assert len([c for c in claims if c.claim_text == 'Adults should reduce ultra-processed foods.']) == 1
