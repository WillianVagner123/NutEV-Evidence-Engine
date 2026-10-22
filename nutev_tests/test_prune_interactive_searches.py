from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import importlib.util

MODULE = Path(__file__).resolve().parents[1] / "tools" / "prune_interactive_searches.py"
spec = importlib.util.spec_from_file_location("prune_interactive_searches", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def _write(root, sid, mode, age_days):
    folder = root / "15_web_searches" / sid
    folder.mkdir(parents=True)
    (folder / "result.json").write_text(json.dumps({
        "search_id": sid, "search_mode": mode,
        "created_at": (datetime.now(timezone.utc)-timedelta(days=age_days)).isoformat()
    }), encoding="utf-8")
    return folder

def test_preview_and_bounded_removal(tmp_path):
    old = _write(tmp_path,"web_old","interactive_bounded",4)
    formal = _write(tmp_path,"web_formal","exact_review_bounded",4)
    recent = _write(tmp_path,"web_new","interactive_bounded",0)
    (tmp_path / "registry").mkdir()
    (tmp_path / "registry" / "article_registry.sqlite").write_bytes(b"scientific")
    preview = module.inventory(tmp_path)
    assert preview["eligible_runs"] == 1 and old.exists()
    applied = module.inventory(tmp_path, apply=True)
    assert applied["removed_runs"] == 1
    assert not old.exists() and formal.exists() and recent.exists()
    assert (tmp_path / "registry" / "article_registry.sqlite").read_bytes() == b"scientific"

def test_never_remove_unknown_modes_or_bad_metadata(tmp_path):
    suspect = _write(tmp_path,"web_unknown","global_exhaustive",8)
    assert module.inventory(tmp_path, apply=True)["removed_runs"] == 0
    assert suspect.exists()
