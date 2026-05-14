from nutev.querypacks.builders import build_querypack


def test_build_querypack():
    tax = {"workstreams": {"busca1": {"base_terms": ["a"], "themes": ["b", "c"]}}}
    qp = build_querypack(tax, ["busca1"])
    assert len(qp["busca1"]) == 2
