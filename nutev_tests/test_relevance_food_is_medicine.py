from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def test_scoring_rules_prioritize_food_is_medicine_interventions() -> None:
    scoring = load_json(Path("config") / "scoring_rules.json")

    for term in [
        "food is medicine",
        "food is medicine intervention",
        "produce prescription",
        "produce prescriptions",
        "produce prescription program",
        "medically tailored meals",
        "medically tailored groceries",
        "teaching kitchen",
        "teaching kitchens",
    ]:
        assert term in scoring["keyword_points"]

    baseline = {
        "title": "Diet intervention for obesity and cardiometabolic risk in adults",
        "abstract": "Lifestyle intervention for obesity management with usual dietary counselling.",
        "source": "pubmed",
        "url": "https://example.org/article",
    }
    food_is_medicine = {
        "title": "Food is medicine produce prescription program with medically tailored meals for adults with obesity and cardiometabolic risk",
        "abstract": "Teaching kitchen support and medically tailored groceries improved dietary adherence.",
        "source": "pubmed",
        "url": "https://example.org/article",
    }

    baseline_scored = score_record(dict(baseline), scoring, "busca2b")
    fim_scored = score_record(dict(food_is_medicine), scoring, "busca2b")

    assert fim_scored["relevance_score"] > baseline_scored["relevance_score"] + 15


def test_food_pharmacy_and_farmacy_terms_enter_search_and_scoring() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")
    scoring = load_json(Path("config") / "scoring_rules.json")

    busca2b = taxonomy["workstreams"]["busca2b"]
    joined_search_terms = " ".join(
        busca2b["focus_terms"] + busca2b["web_query_hints"] + busca2b["document_terms"]
    ).lower()

    for term in [
        "food pharmacy",
        "food pharmacy referral",
        "food farmacy",
        "food farmacy referral",
    ]:
        assert term in joined_search_terms
        assert term in scoring["keyword_points"]
        assert term in scoring["workstream_bonus"]["busca2b"]

    baseline = score_record(
        {
            "title": "Diet intervention for adults with obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring,
        "busca2b",
    )
    expanded = score_record(
        {
            "title": "Food farmacy referral intervention for adults with obesity and cardiometabolic risk",
            "abstract": "Food pharmacy program evaluation measured dietary adherence and nutrition security.",
            "source": "pubmed",
        },
        scoring,
        "busca2b",
    )

    assert expanded["relevance_score"] > baseline["relevance_score"]
