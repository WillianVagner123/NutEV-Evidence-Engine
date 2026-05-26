import json
from pathlib import Path

from nutev.export.curation import _is_prioritized
from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_scoring import score_watch_item
from nutev.querypacks.builders import WORKSTREAM_QUERY_ENHANCEMENTS
from nutev.querypacks.provider_queries import render_queries_for_provider


_CONFIG_ROOT = Path(__file__).resolve().parents[2] / "config"
_ADIPOSITY_CLINICAL_TERMS = {
    "adiposity-based chronic disease",
    "adiposity based chronic disease",
}


def _load_taxonomy() -> dict:
    return json.loads(
        (_CONFIG_ROOT / "keyword_taxonomy.json").read_text(encoding="utf-8")
    )


def test_adiposity_terms_extend_query_and_watch_vocabularies() -> None:
    for workstream in ("busca2a", "busca2b"):
        condition_terms = set(WORKSTREAM_QUERY_ENHANCEMENTS[workstream]["condition_terms"])
        assert _ADIPOSITY_CLINICAL_TERMS <= condition_terms

    watch_terms = set(WATCH_CATEGORIES["obesity_cardiometabolic"])
    assert _ADIPOSITY_CLINICAL_TERMS <= watch_terms

    taxonomy = _load_taxonomy()
    busca2a_queries = render_queries_for_provider(taxonomy, "busca2a", "pubmed")
    busca2b_queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")

    for queries in (busca2a_queries, busca2b_queries):
        assert any(
            term in query for query in queries for term in _ADIPOSITY_CLINICAL_TERMS
        )


def test_adiposity_terms_raise_watch_score_and_curated_priority() -> None:
    baseline = {"title": "General nutrition care model"}
    scoped = {"title": "Adiposity-based chronic disease care model"}

    assert score_watch_item(scoped) > score_watch_item(baseline)
    assert _is_prioritized(
        {
            "title": "Adiposity-based chronic disease management in adults",
            "relevance_score": 8.0,
        }
    )
