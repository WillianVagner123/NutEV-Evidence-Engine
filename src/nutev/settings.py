from __future__ import annotations

from dataclasses import dataclass, field
import json
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


def _merge_unique_list(base: list[Any], override: list[Any]) -> list[Any]:
    output = list(base)
    seen = {str(item).lower() for item in output}
    for item in override:
        marker = str(item).lower()
        if marker in seen:
            continue
        output.append(item)
        seen.add(marker)
    return output


def _deep_merge_config(base: Any, override: Any) -> Any:
    if isinstance(base, dict) and isinstance(override, dict):
        merged = dict(base)
        for key, value in override.items():
            if key in merged:
                merged[key] = _deep_merge_config(merged[key], value)
            else:
                merged[key] = value
        return merged
    if isinstance(base, list) and isinstance(override, list):
        return _merge_unique_list(base, override)
    return override


def load_json(path: Path | str) -> dict:
    config_path = Path(path)
    data = json.loads(config_path.read_text(encoding="utf-8"))
    override_path = config_path.with_name(
        f"{config_path.stem}_overrides{config_path.suffix}"
    )
    if override_path.exists():
        override = json.loads(override_path.read_text(encoding="utf-8"))
        data = _deep_merge_config(data, override)
    return data
