from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


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


def _merge_config_overlay(base: Any, overlay: Any) -> Any:
    if isinstance(base, dict) and isinstance(overlay, dict):
        merged = deepcopy(base)
        for key, value in overlay.items():
            if key in merged:
                merged[key] = _merge_config_overlay(merged[key], value)
            else:
                merged[key] = deepcopy(value)
        return merged
    if isinstance(base, list) and isinstance(overlay, list):
        merged_list = list(base)
        seen = {str(item).lower() for item in merged_list}
        for item in overlay:
            marker = str(item).lower()
            if marker in seen:
                continue
            seen.add(marker)
            merged_list.append(item)
        return merged_list
    return deepcopy(overlay)


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    overlay_path = path.with_name(f"{path.stem}_overlay{path.suffix}")
    if path.name == "keyword_taxonomy.json" and overlay_path.exists():
        overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
        data = _merge_config_overlay(data, overlay)
    return data