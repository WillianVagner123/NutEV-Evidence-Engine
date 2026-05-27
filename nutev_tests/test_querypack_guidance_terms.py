from pathlib import Path

from nutev.pipelines.master_pipeline import _dedup_rows
from nutev.querypacks.builders import build_queries, build_structured_components
from nutev.querypacks.provider_queries import _pubmed_document_clause
from nutev.settings import load_json


def test_busca2a_structured_components_include_high_value_guidance_terms():
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    _, components = build_structured_components(taxonomy, "busca2a")
    doc_terms = {term.lower() for term in components["doc_type_terms"]}
    web_hints = {term.lower() for term in components["web_hints"]}

    assert "consensus statement" in doc_terms
    assert "expert consensus" in doc_terms
    assert "position paper" in doc_terms
    assert "practice guidance" in doc_terms
    assert "guidance statement" in doc_terms
    assert "best practice advice" in doc_terms
    assert "clinical decision pathway" in doc_terms
    assert "standards of care" in doc_terms
    assert "consensus guidance" in doc_terms
    assert "scientific advisory" in doc_terms
    assert "clinical practice recommendations" in doc_terms
    assert "living guideline" in doc_terms
    assert "overview of reviews" in doc_terms
    assert "practice guidance" in web_hints
    assert "guidance statement" in web_hints
    assert "best practice advice" in web_hints
    assert "clinical decision pathway" in web_hints
    assert "standards of care" in web_hints


def test_busca2b_queries_cover_fatty_liver_diet_trials():
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    _, components = build_structured_components(taxonomy, "busca2b")
    condition_terms = {term.lower() for term in components["condition_terms"]}
    queries = [query.lower() for query in build_queries(taxonomy, "busca2b")]

    assert "masld" in condition_terms
    assert "nafld" in condition_terms
    assert "steatotic liver disease" in condition_terms
    assert any(
        ("masld" in query or "nafld" in query or "steatotic liver disease" in query)
        and ("randomized controlled trial" in query or "systematic review" in query)
        for query in queries
    )


def test_busca2b_queries_cover_implementation_readiness_and_sustainment_terms() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    _, components = build_structured_components(taxonomy, "busca2b")
    focus_terms = {term.lower() for term in components["focus_terms"]}
    web_hints = {term.lower() for term in components["web_hints"]}
    queries = [query.lower() for query in build_queries(taxonomy, "busca2b")]

    assert "implementation climate" in focus_terms
    assert "organizational readiness" in focus_terms
    assert "readiness for implementation" in focus_terms
    assert "penetration" in focus_terms
    assert "sustainment" in focus_terms
    assert "organizational readiness" in web_hints
    assert "sustainment" in web_hints
    assert any(
        "implementation climate" in query
        or "organizational readiness" in query
        or "readiness for implementation" in query
        or "penetration" in query
        or "sustainment" in query
        for query in queries
    )


def test_busca1_and_busca2b_cover_food_is_medicine_interventions() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    _, busca1_components = build_structured_components(taxonomy, "busca1")
    _, busca2b_components = build_structured_components(taxonomy, "busca2b")
    busca2b_queries = [query.lower() for query in build_queries(taxonomy, "busca2b")]

    busca1_focus = {term.lower() for term in busca1_components["focus_terms"]}
    busca1_hints = {term.lower() for term in busca1_components["web_hints"]}
    busca2b_focus = {term.lower() for term in busca2b_components["focus_terms"]}
    busca2b_hints = {term.lower() for term in busca2b_components["web_hints"]}

    assert "food is medicine" in busca1_focus
    assert "produce prescription" in busca1_focus
    assert "medically tailored meals" in busca1_focus
    assert "teaching kitchen" in busca1_hints
    assert "food is medicine" in busca2b_focus
    assert "medically tailored groceries" in busca2b_focus
    assert "food is medicine intervention" in busca2b_hints
    assert "produce prescription program" in busca2b_hints
    assert any(
        "food is medicine" in query
        or "produce prescription" in query
        or "medically tailored meals" in query
        for query in busca2b_queries
    )


def test_artigo3_queries_cover_psychometric_and_cross_cultural_terms() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    _, components = build_structured_components(taxonomy, "artigo3_framework")
    focus_terms = {term.lower() for term in components["focus_terms"]}
    web_hints = {term.lower() for term in components["web_hints"]}
    queries = [query.lower() for query in build_queries(taxonomy, "artigo3_framework")]

    assert "cross-cultural adaptation" in focus_terms
    assert "content validity" in focus_terms
    assert "construct validity" in focus_terms
    assert "test-retest reliability" in focus_terms
    assert "measurement invariance" in focus_terms
    assert "cross-cultural adaptation" in web_hints
    assert "measurement invariance" in web_hints
    assert any(
        "cross-cultural adaptation" in query
        or "content validity" in query
        or "construct validity" in query
        or "test-retest reliability" in query
        or "measurement invariance" in query
        for query in queries
    )


def test_pubmed_document_clause_maps_new_guidance_and_review_terms():
    clause = _pubmed_document_clause(
        [
            "consensus statement",
            "practice advisory",
            "practice guidance",
            "guidance statement",
            "clinical decision pathway",
            "position paper",
            "umbrella review",
            "consensus guidance",
            "consensus report",
            "clinical practice recommendation",
            "clinical practice recommendations",
            "guideline update",
            "clinical practice update",
            "standards of care",
            "standards of medical care in diabetes",
            "scientific advisory",
            "best practice advice",
            "meta analysis",
            "network meta-analysis",
            "network meta analysis",
        ]
    ).lower()

    assert '"consensus"[publication type]' in clause
    assert '"practice guideline"[publication type]' in clause
    assert '"guideline"[publication type]' in clause
    assert '"systematic review"[publication type]' in clause
    assert '"meta-analysis"[publication type]' in clause
    assert '"scientific advisory"[title/abstract]' in clause
    assert '"best practice advice"[title/abstract]' in clause
    assert '"consensus guidance"[title/abstract]' not in clause
    assert '"consensus report"[title/abstract]' not in clause
    assert '"clinical practice recommendation"[title/abstract]' not in clause
    assert '"clinical practice recommendations"[title/abstract]' not in clause
    assert '"guideline update"[title/abstract]' not in clause
    assert '"clinical practice update"[title/abstract]' not in clause
    assert '"standards of care"[title/abstract]' not in clause
    assert '"standards of medical care in diabetes"[title/abstract]' not in clause
    assert '"meta analysis"[title/abstract]' not in clause
    assert '"network meta-analysis"[title/abstract]' not in clause
    assert '"network meta analysis"[title/abstract]' not in clause


def test_master_pipeline_dedup_normalizes_doi_and_url_before_title_year():
    rows = [
        {
            "title": "Lifestyle Medicine Consensus 2024",
            "year": 2024,
            "doi": "https://doi.org/10.1000/ABC",
            "url": "https://example.org/paper?utm_source=watch",
            "source": "pubmed",
        },
        {
            "title": "Lifestyle Medicine Consensus Updated Title",
            "year": 2024,
            "doi": "10.1000/abc",
            "url": "https://example.org/paper/",
            "source": "openalex",
        },
    ]

    deduped = _dedup_rows(rows)

    assert len(deduped) == 1
    assert deduped[0]["source"] == "pubmed"


def test_master_pipeline_dedup_keeps_distinct_blank_identity_rows():
    rows = [
        {"title": "", "year": "", "url": "", "source": "pubmed"},
        {"title": "", "year": "", "url": "", "source": "crossref"},
    ]

    deduped = _dedup_rows(rows)

    assert len(deduped) == 2
