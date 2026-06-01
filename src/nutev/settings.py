from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
from copy import deepcopy


@dataclass
class NutevSettings:
    project_root: Path
    config_root: Path = Path("config")
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


def _merge_unique_lists(base: list, overlay: list) -> list:
    merged = list(base)
    seen = {str(item).strip().lower() for item in merged if str(item).strip()}
    for item in overlay:
        value = str(item).strip()
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged


def _deep_merge_config(base: dict, overlay: dict) -> dict:
    merged = deepcopy(base)
    for key, value in overlay.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = _deep_merge_config(current, value)
        elif isinstance(current, list) and isinstance(value, list):
            merged[key] = _merge_unique_lists(current, value)
        else:
            merged[key] = deepcopy(value)
    return merged


def _load_optional_overlay(path: Path) -> dict:
    overlay_path = path.with_name(f"{path.stem}_overlay{path.suffix}")
    if not overlay_path.exists():
        return {}
    return json.loads(overlay_path.read_text(encoding="utf-8"))


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    overlay = _load_optional_overlay(path)
    if overlay:
        return _deep_merge_config(data, overlay)
    return data
