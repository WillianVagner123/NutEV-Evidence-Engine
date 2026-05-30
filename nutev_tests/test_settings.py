from __future__ import annotations

import os
from pathlib import Path

import pytest

from nutev.settings import load_json


def test_load_json_resolves_repo_relative_config_from_other_cwd(tmp_path: Path) -> None:
    previous_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        data = load_json(Path("config/scoring_rules.json"))
    finally:
        os.chdir(previous_cwd)

    assert "keyword_points" in data


def test_load_json_reports_attempted_paths(tmp_path: Path) -> None:
    missing = tmp_path / "missing_config.json"

    with pytest.raises(FileNotFoundError) as exc_info:
        load_json(missing)

    message = str(exc_info.value)
    assert "Config JSON not found" in message
    assert str(missing) in message
