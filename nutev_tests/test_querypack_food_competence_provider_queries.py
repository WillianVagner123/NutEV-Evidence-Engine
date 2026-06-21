from __future__ import annotations

import json
from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider


def test_provider_querypack_includes_food_competence_terms_for_article3() -> None:
    taxonomy = json.loads(Path("config/keyword_taxonomy.json").read_text(encoding="utf-8"))

    queries = render_queries_for_provider(taxonomy, "artigo3_framework", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "food competence" in rendered
    assert "eating competence" in rendered
    assert "food preparation self-efficacy" in rendered
    assert "cooking self-efficacy questionnaire" in rendered
