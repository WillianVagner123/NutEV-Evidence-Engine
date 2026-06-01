from __future__ import annotations

from pathlib import Path

from nutev.search.checkpoint import load_checkpoint, save_checkpoint


def test_corrupt_checkpoint_is_ignored_and_renamed(tmp_path: Path):
    path = tmp_path / "bad.json"
    path.write_text("{not-json", encoding="utf-8")
    assert load_checkpoint(path) is None
    assert not path.exists() or path.with_suffix(".json.corrupt").exists()


def test_checkpoint_roundtrip(tmp_path: Path):
    path = tmp_path / "provider" / "x.json"
    save_checkpoint(path, {"status": "partial", "rows": [{"pmid": "1"}]})
    data = load_checkpoint(path)
    assert data and data["status"] == "partial"
    assert data["rows"][0]["pmid"] == "1"
