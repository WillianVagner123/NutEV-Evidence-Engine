from pathlib import Path

from nutev.global_watch.watch_pipeline import infer_workstream_affinity
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def test_busca2b_pubmed_queries_include_liver_terms_from_tail_conditions():
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "masld" in rendered
    assert "nafld" in rendered
    assert "mafld" in rendered
    assert "mash" in rendered
    assert "nash" in rendered
    assert "steatotic liver disease" in rendered
    assert "metabolic dysfunction-associated steatohepatitis" in rendered
    assert "non-alcoholic fatty liver disease" in rendered
    assert "nonalcoholic steatohepatitis" in rendered


def test_busca2b_pubmed_queries_include_hepatic_steatosis_nutrition_terms():
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "hepatic steatosis" in rendered
    assert "liver fat reduction" in rendered
    assert "dietary intervention for hepatic steatosis" in rendered
    assert "nutrition intervention for hepatic steatosis" in rendered


def test_watch_affinity_maps_metabolic_liver_nutrition_interventions_to_busca2b():
    affinity = infer_workstream_affinity(
        "Medical nutrition therapy for MASLD and non-alcoholic steatohepatitis in adults",
        "diet_patterns",
    )

    assert "busca2b" in affinity
