from nutev.analysis.relevance import keep_candidate_for_download, score_record


def _base_record(title: str, abstract: str = "") -> dict:
    return {
        "title": title,
        "abstract": abstract,
        "source": "pubmed",
        "url": "https://example.org/article",
        "doi": "10.1000/example",
        "journal": "Nutrition Journal",
        "source_institution": "",
    }


def test_busca2a_adiposity_guidelines_gain_priority() -> None:
    baseline = score_record(
        _base_record(
            "Clinical practice guideline for adults with obesity and dyslipidemia",
            "Medical nutrition therapy and blood pressure outcomes were reviewed.",
        ),
        {},
        "busca2a",
    )
    enriched = score_record(
        _base_record(
            "Clinical practice guideline for weight management in adults with adiposity-based chronic disease and dyslipidemia",
            "Medical nutrition therapy and blood pressure outcomes were reviewed.",
        ),
        {},
        "busca2a",
    )

    assert enriched["relevance_score"] > baseline["relevance_score"]
    assert keep_candidate_for_download(enriched, "busca2a") is True


def test_busca2b_weight_maintenance_trials_gain_priority() -> None:
    baseline = score_record(
        _base_record(
            "Randomized trial of nutrition counseling for adults with obesity and type 2 diabetes",
            "Adherence and lifestyle modification outcomes were assessed.",
        ),
        {},
        "busca2b",
    )
    enriched = score_record(
        _base_record(
            "Randomized trial of weight-loss maintenance and weight regain prevention in adults with adiposity-based chronic disease and type 2 diabetes",
            "Adherence and lifestyle modification outcomes were assessed.",
        ),
        {},
        "busca2b",
    )

    assert enriched["relevance_score"] > baseline["relevance_score"]
    assert keep_candidate_for_download(enriched, "busca2b") is True
