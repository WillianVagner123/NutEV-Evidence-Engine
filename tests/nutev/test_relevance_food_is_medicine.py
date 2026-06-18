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


def test_busca1_food_is_medicine_delivery_models_gain_priority() -> None:
    baseline = score_record(
        _base_record(
            "Community healthy eating policy report for adults with obesity",
            "Food literacy and meal planning support in primary care.",
        ),
        {},
        "busca1",
    )
    enriched = score_record(
        _base_record(
            "Food is medicine produce prescription and teaching kitchen policy report for adults with obesity",
            "Food literacy and medically tailored meals support in primary care.",
        ),
        {},
        "busca1",
    )

    assert enriched["relevance_score"] > baseline["relevance_score"]


def test_busca2b_food_is_medicine_trials_stay_download_eligible() -> None:
    baseline = score_record(
        _base_record(
            "Randomized trial of nutrition counseling for adults with obesity and type 2 diabetes",
            "Adherence and implementation outcomes were assessed.",
        ),
        {},
        "busca2b",
    )
    enriched = score_record(
        _base_record(
            "Randomized trial of medically tailored meals and produce prescription for adults with obesity and type 2 diabetes",
            "Adherence, implementation outcomes, and teaching kitchen support were assessed.",
        ),
        {},
        "busca2b",
    )

    assert enriched["relevance_score"] > baseline["relevance_score"]
    assert keep_candidate_for_download(enriched, "busca2b") is True


def test_busca2b_food_is_medicine_referral_economics_gain_priority() -> None:
    baseline = score_record(
        _base_record(
            "Implementation evaluation of nutrition counseling for adults with obesity and type 2 diabetes",
            "Primary care referral workflows and adherence outcomes were assessed.",
        ),
        {},
        "busca2b",
    )
    enriched = score_record(
        _base_record(
            "Implementation evaluation of food is medicine referral through a food pharmacy for adults with obesity and type 2 diabetes",
            "Produce prescription referral, medically tailored meals cost-effectiveness, healthcare utilization, and adherence outcomes were assessed.",
        ),
        {},
        "busca2b",
    )

    assert enriched["relevance_score"] > baseline["relevance_score"] + 20
    assert keep_candidate_for_download(enriched, "busca2b") is True
