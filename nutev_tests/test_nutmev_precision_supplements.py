from __future__ import annotations

from pathlib import Path

from nutev.querypacks.builders import build_querypack
from nutev.settings import load_json


CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"


def test_precision_taxonomy_supplement_reaches_querypack() -> None:
    taxonomy = load_json(CONFIG_DIR / "keyword_taxonomy.json")

    queries = build_querypack(taxonomy, ["busca2b", "a3"])
    busca2b_query_text = "\n".join(queries["busca2b"]).lower()
    a3_query_text = "\n".join(queries["a3"]).lower()

    assert "dietary self-regulation" in busca2b_query_text
    assert "habit formation" in busca2b_query_text
    assert "type 2 diabetes remission" in busca2b_query_text
    assert "ckm syndrome" in busca2b_query_text
    assert "food preparation skills" in a3_query_text
    assert "food label literacy" in a3_query_text


def test_precision_scoring_supplement_adds_keyword_points() -> None:
    scoring = load_json(CONFIG_DIR / "scoring_rules.json")
    keyword_points = scoring["keyword_points"]

    assert keyword_points["dietary self-regulation"] == 3
    assert keyword_points["habit formation"] == 3
    assert keyword_points["ckm syndrome"] == 4
    assert keyword_points["type 2 diabetes remission"] == 4
    assert keyword_points["food preparation skills"] == 3
