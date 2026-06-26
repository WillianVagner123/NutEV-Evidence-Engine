from __future__ import annotations

import json
from pathlib import Path


def _load_supplement() -> dict:
    path = (
        Path(__file__).resolve().parents[1]
        / "config"
        / "keyword_taxonomy_supplement_ckm_kidney_20260626.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_ckm_kidney_supplement_targets_clinical_guideline_workstream() -> None:
    supplement = _load_supplement()
    busca2a = supplement["workstreams"]["busca2a"]

    assert "chronic kidney disease" in busca2a["condition_terms"]
    assert "diabetic kidney disease" in busca2a["condition_terms"]
    assert "cardiovascular-kidney-metabolic disease" in busca2a["condition_terms"]
    assert "chronic kidney disease nutrition guideline" in busca2a["web_query_hints"]
    assert "scientific statement" in busca2a["document_terms"]


def test_ckm_kidney_supplement_targets_intervention_workstream() -> None:
    supplement = _load_supplement()
    busca2b = supplement["workstreams"]["busca2b"]

    assert "ckd" in busca2b["condition_terms"]
    assert "medical nutrition therapy diabetic kidney disease" in busca2b["focus_terms"]
    assert "lifestyle intervention ckd" in busca2b["focus_terms"]
    assert (
        "chronic kidney disease dietary intervention systematic review"
        in busca2b["web_query_hints"]
    )
    assert "randomized trial" in busca2b["document_terms"]
