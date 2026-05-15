from nutev.engine.ids import make_document_id


def test_document_id_stable_for_doi():
    a = make_document_id({"doi": "10.1000/ABC"})
    b = make_document_id({"doi": "https://doi.org/10.1000/abc"})
    assert a == b


def test_document_id_stable_for_url():
    a = make_document_id({"final_url": "https://Example.com/paper/"})
    b = make_document_id({"final_url": "https://example.com/paper"})
    assert a == b
