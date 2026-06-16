from __future__ import annotations

from pathlib import Path

from nutev.querypacks.builders import build_queries, build_structured_components
from nutev.settings import load_json


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json"


def test_ckm_supplement_extends_busca2_query_components() -> None:
    taxonomy = load_json(CONFIG_PATH)

    for workstream in ("busca2a", "busca2b"):
        workstream_config = taxonomy["workstreams"][workstream]
        assert "cardiometabolic" in workstream_config["clinical_keys"]
        assert "cardiometabolic" in workstream_config["priority_outcomes"]

        _, components = build_structured_components(taxonomy, workstream)
        assert "cardiovascular-kidney-metabolic syndrome" in components["clinical_terms"]
        assert "ckm health" in components["priority_outcomes"]

        query_text = "\n".join(build_queries(taxonomy, workstream)).lower()
        assert "cardiovascular-kidney-metabolic syndrome" in query_text
        assert "ckm health" in query_text
