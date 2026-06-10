from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def default_config_root() -> Path:
    return Path(__file__).resolve().parents[2] / "config"


@dataclass
class NutevSettings:
    project_root: Path
    config_root: Path = field(default_factory=default_config_root)
    web_enabled: bool = False
    mode: str = "thesis"
    since_days: int = 30
    browser_enabled: bool = False
    llm_enabled: bool = False

    @property
    def output_dirs(self) -> dict[str, Path]:
        b = self.project_root
        return {
            "00_config": b / "00_config",
            "01_querypacks": b / "01_querypacks",
            "02_metadata": b / "02_metadata",
            "03A_metadata_hits": b / "03_corpus" / "03A_metadata_hits",
            "03B_public_downloads": b / "03_corpus" / "03B_public_downloads",
            "03C_official_docs": b / "03_corpus" / "03C_official_docs",
            "03D_manual_uploads": b / "03_corpus" / "03D_manual_uploads",
            "04_ocr_text": b / "04_ocr_text",
            "05_extraction": b / "05_extraction",
            "06_tables": b / "06_tables",
            "07_logs": b / "07_logs",
            "08_docs": b / "08_docs",
            "10_curated": b / "10_curated",
        }


def _merge_dict(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_json(path: Path | str) -> dict:
    config_path = Path(path)
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if config_path.name != "scoring_rules.json":
        return data

    overlay_path = config_path.with_name("scoring_rules_overlay.json")
    if not overlay_path.exists():
        return data

    overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
    return _merge_dict(data, overlay)
