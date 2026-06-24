from __future__ import annotations

from nutev.analysis.relevance import score_record
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import default_config_root, load_json


def test_ckm_supplement_feeds_clinical_provider_queries() -> None:
    taxonomy = load_json(default_config_root() / "keyword_taxonomy.json")

    busca2a_queries = "\n".join(
        render_queries_for_provider(taxonomy, "busca2a", "pubmed")
    ).lower()
    busca2b_queries = "\n".join(
        render_queries_for_provider(taxonomy, "busca2b", "europepmc")
    ).lower()

    assert "cardiovascular-kidney-metabolic" in busca2a_queries
    assert "chronic kidney disease" in busca2a_queries
    assert "ckm syndrome" in busca2b_queries
    assert "diabetic kidney disease" in busca2b_queries


def test_ckm_supplement_improves_clinical_priority_score() -> None:
    scoring = load_json(default_config_root() / "scoring_rules.json")
    ckm_record = {
        "source": "pubmed",
        "title": "Cardiovascular-kidney-metabolic syndrome nutrition practice guideline for obesity and chronic kidney disease",
        "abstract": "Medical nutrition therapy and therapeutic lifestyle changes for cardiometabolic risk and diabetic kidney disease.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/example",
    }
    baseline_record = {
        "source": "pubmed",
        "title": "Nutrition practice guideline for obesity",
        "abstract": "Medical nutrition therapy and therapeutic lifestyle changes for cardiometabolic risk.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/example",
    }

    ckm_score = score_record(dict(ckm_record), scoring, "busca2a")["relevance_score"]
    baseline_score = score_record(dict(baseline_record), scoring, "busca2a")["relevance_score"]

    assert ckm_score > baseline_score
