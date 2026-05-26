from __future__ import annotations

from pathlib import Path

from nutev.global_watch.watch_scoring import score_watch_item
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


KEYWORD_TAXONOMY_PATH = Path("config") / "keyword_taxonomy.json"


def test_busca2b_pubmed_queries_include_lifestyle_medicine_variants() -> None:
    taxonomy = load_json(KEYWORD_TAXONOMY_PATH)

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    rendered = "\n".join(queries).lower()

    assert '"lifestyle medicine intervention"[title/abstract]' in rendered
    assert '"lifestyle medicine programme"[title/abstract]' in rendered
    assert '"lifestyle medicine counselling"[title/abstract]' in rendered


def test_watch_scoring_rewards_lifestyle_medicine_variants() -> None:
    plain_score = score_watch_item(
        {
            "title": "Nutrition care note",
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )
    enriched_score = score_watch_item(
        {
            "title": "Lifestyle medicine intervention programme for cardiometabolic risk",
            "abstract": (
                "Lifestyle medicine counselling and a structured lifestyle medicine "
                "approach supported long-term adherence."
            ),
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )

    assert enriched_score > plain_score + 40
