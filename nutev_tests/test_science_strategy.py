import json
from pathlib import Path

from nutev.analysis.domains_busca1 import apply_domain_rules as apply_busca1_domain_rules
from nutev.analysis.relevance import keep_candidate_for_download, score_record
from nutev.search.official_sources import manifest_sources


def test_manifest_sources_supports_a3_aliases():
    manifest = {
        "workstreams": {
            "artigo3_framework": [
                {"name": "Lifestyle medicine competencies", "url": "https://example.org/a3", "authority": 4}
            ]
        }
    }

    rows = manifest_sources(manifest, "a3")

    assert len(rows) == 1
    assert rows[0]["source"] == "official"
    assert rows[0]["title"] == "Lifestyle medicine competencies"


def test_busca1_domain_rules_capture_behavioral_and_culinary_signals():
    rules = {
        "domains": {
            "adesao_implementacao": ["adherence", "implementation", "behavior change"],
            "literacia_culinaria_comensalidade": ["food literacy", "culinary medicine", "commensality"],
        }
    }
    rows = [
        {
            "title": "Lifestyle medicine food literacy implementation framework",
            "extracted_text": "This culinary medicine intervention improved adherence and behavior change in shared meals context.",
        }
    ]

    out = apply_busca1_domain_rules(rows, rules)

    assert out[0]["domain_adesao_implementacao_present"] == 1
    assert out[0]["domain_literacia_culinaria_comensalidade_present"] == 1
    assert out[0]["domain_adesao_implementacao_count"] >= 2


def test_relevance_scoring_uses_abstract_and_extracted_text_for_scientific_priority():
    record = {
        "source": "pubmed",
        "title": "Diet intervention in adults",
        "url": "https://example.org/study.pdf",
        "abstract": "Clinical practice guideline for obesity and cardiometabolic risk with adherence, implementation and food literacy outcomes.",
        "extracted_text": "Systematic review and implementation science evidence for Mediterranean diet and DASH in adults with obesity and hypertension.",
    }

    scored = score_record(record, {"keyword_points": {}, "source_points": {}, "workstream_points": {}}, "busca2b")

    assert scored["relevance_score"] >= 35
    assert keep_candidate_for_download(scored, "busca2b") is True


def test_relevance_scoring_drops_pediatric_editorial_noise():
    record = {
        "source": "crossref",
        "title": "Editorial on pediatric obesity commentary",
        "url": "https://example.org/editorial",
        "abstract": "Commentary letter about child obesity.",
        "extracted_text": "",
    }

    scored = score_record(record, {"keyword_points": {}, "source_points": {}, "workstream_points": {}}, "busca2a")

    assert keep_candidate_for_download(scored, "busca2a") is False
