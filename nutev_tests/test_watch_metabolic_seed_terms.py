from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_obesity_cardiometabolic_watch_terms_include_glycemic_risk_variants():
    terms = {term.lower() for term in WATCH_CATEGORIES["obesity_cardiometabolic"]}

    expected_terms = {
        "type 2 diabetes mellitus",
        "diabetes mellitus type 2",
        "t2d",
        "t2dm",
        "diabesity",
        "pre-diabetes",
        "prediabetic state",
        "impaired fasting glucose",
        "impaired glucose tolerance",
        "dysglycemia",
        "dysglycaemia",
        "glycemic control",
        "glycaemic control",
        "hba1c",
    }

    assert expected_terms <= terms
