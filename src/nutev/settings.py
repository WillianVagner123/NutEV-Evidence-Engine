from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import json
import sys


def default_config_root() -> Path:
    # In a PyInstaller bundle the package lives under _MEIPASS and there is no
    # repo root above it, so config/ is shipped at the bundle root instead.
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "config"
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
            "09_global_watch": b / "09_global_watch",
            "10_curated": b / "10_curated",
            "11_knowledge_base": b / "11_knowledge_base",
        }


def _merge_config(base: dict, supplement: dict) -> dict:
    merged = dict(base)
    for key, value in supplement.items():
        if key == "version_note":
            continue
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_config(merged[key], value)
            continue
        if isinstance(value, list) and isinstance(merged.get(key), list):
            existing = list(merged[key])
            seen = {str(item).strip().lower() for item in existing}
            for item in value:
                normalized = str(item).strip().lower()
                if normalized and normalized not in seen:
                    existing.append(item)
                    seen.add(normalized)
            merged[key] = existing
            continue
        merged[key] = value
    return merged


def _load_keyword_taxonomy_supplement(path: Path) -> dict:
    supplement_path = path.with_name("keyword_taxonomy_supplement.json")
    if not supplement_path.exists():
        return {}
    return json.loads(supplement_path.read_text(encoding="utf-8"))


def load_json(path: Path | str) -> dict:
    json_path = Path(path)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    if json_path.name == "keyword_taxonomy.json":
        supplement = _load_keyword_taxonomy_supplement(json_path)
        if supplement:
            data = _merge_config(data, supplement)
    return data
