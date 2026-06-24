from pathlib import Path

from nutev.analysis.relevance import keep_candidate_for_download, score_record
from nutev.settings import load_json


def _scoring_rules() -> dict:
    return load_json(Path("config") / "scoring_rules.json")


def test_busca2b_prioritizes_diet_linked_metabolic_remission_trials() -> None:
    rules = _scoring_rules()
    baseline = score_record(
        {
            "source": "pubmed",
            "title": "Randomized trial of nutrition counseling for adults with obesity and type 2 diabetes",
            "abstract": "Adherence and implementation outcomes were assessed after lifestyle intervention.",
            "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/",
        },
        rules,
        "busca2b",
    )
    remission = score_record(
        {
            "source": "pubmed",
            "title": "Diet-induced diabetes remission maintenance after weight loss maintenance intervention",
            "abstract": "Adults with obesity and type 2 diabetes received lifestyle-induced diabetes remission support with dietary adherence follow-up.",
            "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7654321/",
        },
        rules,
        "busca2b",
    )

    assert remission["relevance_score"] > baseline["relevance_score"]
    assert keep_candidate_for_download(remission, "busca2b") is True


def test_busca2a_prioritizes_remission_guidance_for_clinical_mapping() -> None:
    rules = _scoring_rules()
    scored = score_record(
        {
            "source": "pubmed",
            "title": "Type 2 diabetes remission consensus guideline for adults with obesity",
            "abstract": "Clinical practice recommendations address weight loss maintenance and cardiometabolic risk management.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/123456/",
        },
        rules,
        "busca2a",
    )

    assert scored["relevance_score"] >= 25
    assert scored["out_of_scope_flags"] == []
