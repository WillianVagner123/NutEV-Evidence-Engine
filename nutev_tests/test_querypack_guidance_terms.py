from pathlib import Path

from nutev.pipelines.master_pipeline import _dedup_rows
from nutev.querypacks.builders import build_structured_components
from nutev.querypacks.provider_queries import _pubmed_document_clause
from nutev.settings import load_json


def test_busca2a_structured_components_include_high_value_guidance_terms():
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    _, components = build_structured_components(taxonomy, "busca2a")
    doc_terms = {term.lower() for term in components["doc_type_terms"]}

    assert "consensus statement" in doc_terms
    assert "expert consensus" in doc_terms
    assert "position paper" in doc_terms
    assert "practice advisory" in doc_terms
    assert "living guideline" in doc_terms
    assert "overview of reviews" in doc_terms


def test_pubmed_document_clause_maps_new_guidance_and_review_terms():
    clause = _pubmed_document_clause(
        [
            "consensus statement",
            "practice advisory",
            "position paper",
            "umbrella review",
        ]
    ).lower()

    assert '"consensus"[publication type]' in clause
    assert '"practice guideline"[publication type]' in clause
    assert '"guideline"[publication type]' in clause
    assert '"systematic review"[publication type]' in clause


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
