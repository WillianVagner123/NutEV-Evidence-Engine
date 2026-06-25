from __future__ import annotations

import json

from nutev.search.checkpoint import load_checkpoint, save_checkpoint


def test_save_checkpoint_writes_sorted_keys_and_remains_loadable(tmp_path) -> None:
    path = tmp_path / "pubmed" / "checkpoint.json"

    save_checkpoint(path, {"zeta": 1, "alpha": 2})

    text = path.read_text(encoding="utf-8")
    payload = json.loads(text)
    assert payload["alpha"] == 2
    assert payload["zeta"] == 1
    assert "updated_at" in payload
    assert text.index('"alpha"') < text.index('"updated_at"') < text.index('"zeta"')
    assert load_checkpoint(path) == payload
