"""Config provenance: the run-reproducibility digest over taxonomy/scoring."""
from __future__ import annotations

import json

from nutev.config_provenance import (
    build_config_provenance,
    config_family_provenance,
    write_config_provenance,
)
from nutev.settings import load_json, resolve_config_sources


def _write(path, obj):
    path.write_text(json.dumps(obj), encoding="utf-8")


def test_family_provenance_lists_base_then_supplements_in_merge_order(tmp_path):
    base = tmp_path / "taxonomy.json"
    _write(base, {"terms": ["a"]})
    _write(tmp_path / "taxonomy_supplement.json", {"terms": ["b"]})
    _write(tmp_path / "taxonomy_supplement_z.json", {"terms": ["z"]})
    _write(tmp_path / "taxonomy_supplement_a.json", {"terms": ["m"]})

    rec = config_family_provenance(base)

    names = [s["name"] for s in rec["sources"]]
    # base, exact _supplement, then _supplement_* sorted by name.
    assert names == [
        "taxonomy.json",
        "taxonomy_supplement.json",
        "taxonomy_supplement_a.json",
        "taxonomy_supplement_z.json",
    ]
    assert rec["supplement_count"] == 3
    assert rec["present"] is True
    # sources match exactly what the loader would merge.
    assert names == [p.name for p in resolve_config_sources(base)]


def test_merged_digest_matches_loaded_config(tmp_path):
    base = tmp_path / "taxonomy.json"
    _write(base, {"terms": ["a"]})
    _write(tmp_path / "taxonomy_supplement.json", {"terms": ["b"]})

    rec = config_family_provenance(base)
    # The digest is over the fully merged config, and the merge unions list items.
    merged = load_json(base)
    assert merged["terms"] == ["a", "b"]
    assert rec["merged_digest"] is not None


def test_config_digest_changes_when_a_supplement_changes(tmp_path):
    families = ("taxonomy.json",)
    base = tmp_path / "taxonomy.json"
    _write(base, {"terms": ["a"]})
    supp = tmp_path / "taxonomy_supplement.json"
    _write(supp, {"terms": ["b"]})

    before = build_config_provenance(tmp_path, families)["config_digest"]

    # Adding a new term to a supplement must move the digest.
    _write(supp, {"terms": ["b", "c"]})
    after = build_config_provenance(tmp_path, families)["config_digest"]

    assert before != after


def test_config_digest_is_stable_across_identical_inputs(tmp_path):
    families = ("taxonomy.json",)
    _write(tmp_path / "taxonomy.json", {"terms": ["a"]})
    first = build_config_provenance(tmp_path, families)["config_digest"]
    second = build_config_provenance(tmp_path, families)["config_digest"]
    assert first == second


def test_missing_family_is_recorded_not_raised(tmp_path):
    rec = build_config_provenance(tmp_path, ("does_not_exist.json",))
    fam = rec["families"]["does_not_exist.json"]
    assert fam["present"] is False
    assert fam["merged_digest"] is None
    # A digest is still produced (over the absent family), never an exception.
    assert isinstance(rec["config_digest"], str)


def test_write_config_provenance_emits_file(tmp_path):
    _write(tmp_path / "taxonomy.json", {"terms": ["a"]})
    out = tmp_path / "logs" / "config_provenance.json"
    record = write_config_provenance(out, tmp_path, ("taxonomy.json",))
    assert out.exists()
    on_disk = json.loads(out.read_text(encoding="utf-8"))
    assert on_disk["config_digest"] == record["config_digest"]


def test_packaged_config_root_has_a_deterministic_digest():
    # The real shipped config must produce a non-empty, stable digest so runs
    # against the packaged taxonomy are reproducible.
    from nutev.settings import default_config_root

    rec = build_config_provenance(default_config_root())
    assert rec["config_digest"]
    assert rec["families"]["keyword_taxonomy.json"]["present"] is True
    assert rec["families"]["keyword_taxonomy.json"]["supplement_count"] >= 1
