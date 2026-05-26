from __future__ import annotations

import json
from pathlib import Path

from nutev.export.curation import _is_prioritized
from nutev.querypacks.builders import build_structured_components


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KEYWORD_TAXONOMY_PATH = PROJECT_ROOT / "config" / "keyword_taxonomy.json"


def _load_keyword_taxonomy() -> dict:
    return json.loads(KEYWORD_TAXONOMY_PATH.read_text(encoding="utf-8"))


def test_busca2b_auto_includes_fatty_liver_clinical_terms() -> None:
    taxonomy = _load_keyword_taxonomy()
    _, components = build_structured_components(taxonomy, "busca2b")

    clinical_terms = {term.lower() for term in components["clinical_terms"]}

    assert "masld" in clinical_terms
    assert "mash" in clinical_terms
    assert "steatotic liver disease" in clinical_terms


def test_curation_prioritizes_mash_and_mafld_documents() -> None:
    row = {
        "title": "Dietary intervention for MASH and metabolic dysfunction-associated fatty liver disease",
        "clinical_conditions": "MASH; metabolic dysfunction-associated fatty liver disease",
        "relevance_score": 9,
    }

    assert _is_prioritized(row) is True
