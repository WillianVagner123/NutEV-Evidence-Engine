from __future__ import annotations

import json

from nutev.settings import default_config_root
from nutev.taxonomy import (
    build_all,
    build_multilingual_lexicon,
    build_ontology,
    build_openalex_cache,
    concept_scores,
    concept_summary,
    load_taxonomy,
    validate_taxonomy,
)

CONFIG = default_config_root()


def test_master_reproduces_current_derived_files():
    """The generator must reproduce the committed derived files (no test breaks)."""
    tax = load_taxonomy(CONFIG)
    assert build_multilingual_lexicon(tax) == json.loads((CONFIG / "multilingual_lexicon.json").read_text(encoding="utf-8"))
    assert build_ontology(tax) == json.loads((CONFIG / "nutev_ontology.json").read_text(encoding="utf-8"))


def test_real_taxonomy_is_valid():
    assert validate_taxonomy(load_taxonomy(CONFIG)) == []


def test_concept_summary_groups_by_type():
    summary = concept_summary(load_taxonomy(CONFIG))
    assert "type 2 diabetes" in summary["condition"]
    assert "mediterranean diet" in summary["diet"]


def test_validate_catches_problems():
    bad = {
        "languages": ["en", "pt"],
        "concepts": [
            {"id": "x", "type": "condition", "terms": {"en": ["x"]}},  # missing pt
            {"id": "x", "type": "bogus", "terms": {"en": ["y"], "pt": ["y"]}},  # dup id + bad type
            {"id": "z", "type": "diet", "terms": {"pt": ["z"]}},  # missing en
        ],
        "ontology": {"domains": {}, "evidence_types": []},
    }
    errors = validate_taxonomy(bad)
    joined = " | ".join(errors)
    assert "missing terms for languages" in joined  # concept x missing pt
    assert "duplicate concept id" in joined
    assert "invalid type" in joined
    assert "terms.en" in joined  # concept z missing english


def _write_tax(config_dir, concepts, ontology=None):
    tax = {
        "version": "1.0",
        "languages": ["en", "pt"],
        "lexicon_comment": "test",
        "concepts": concepts,
        "ontology": ontology or {"domains": {"d": ["a"]}, "evidence_types": ["rct"]},
    }
    (config_dir / "taxonomy.json").write_text(json.dumps(tax), encoding="utf-8")
    return tax


def test_build_all_regenerates_files(tmp_path):
    _write_tax(
        tmp_path,
        [
            {"id": "obesity", "type": "condition", "mesh": "Obesity", "terms": {"en": ["obesity"], "pt": ["obesidade"]}},
            {"id": "dash diet", "type": "diet", "terms": {"en": ["dash"], "pt": ["dash"]}},
        ],
    )
    written = build_all(tmp_path)
    assert "multilingual_lexicon" in written and "nutev_ontology" in written
    lex = json.loads((tmp_path / "multilingual_lexicon.json").read_text(encoding="utf-8"))
    assert lex["concept_groups"]["conditions"] == ["obesity"]
    assert lex["concept_groups"]["diets"] == ["dash diet"]
    assert lex["mesh"] == {"obesity": "Obesity"}  # only the concept with a mesh
    assert lex["concepts"]["obesity"]["pt"] == ["obesidade"]


def test_build_all_seeds_openalex_and_scores(tmp_path):
    _write_tax(
        tmp_path,
        [
            {"id": "obesity", "type": "condition", "terms": {"en": ["obesity"], "pt": ["obesidade"]},
             "openalex": "C123", "score": 7},
        ],
    )
    (tmp_path / "scoring_rules.json").write_text(json.dumps({"keyword_points": {"existing": 1}}), encoding="utf-8")
    written = build_all(tmp_path)
    # scores merged additively (existing preserved)
    scoring = json.loads((tmp_path / "scoring_rules.json").read_text(encoding="utf-8"))
    assert scoring["keyword_points"]["obesity"] == 7
    assert scoring["keyword_points"]["existing"] == 1
    assert "scoring_rules" in written
    # openalex cache seeded (lowercased id + english term)
    cache = json.loads((tmp_path / "openalex_concepts.json").read_text(encoding="utf-8"))
    assert cache["obesity"] == "C123"


def test_no_scores_does_not_touch_scoring(tmp_path):
    _write_tax(tmp_path, [{"id": "obesity", "type": "condition", "terms": {"en": ["o"], "pt": ["o"]}}])
    (tmp_path / "scoring_rules.json").write_text(json.dumps({"keyword_points": {"existing": 1}}), encoding="utf-8")
    written = build_all(tmp_path)
    assert "scoring_rules" not in written  # untouched when no concept declares a score
    assert concept_scores(load_taxonomy(tmp_path)) == {}
    assert build_openalex_cache(load_taxonomy(tmp_path)) == {}
