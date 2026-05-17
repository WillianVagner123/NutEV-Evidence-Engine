from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json

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
        base = self.project_root
        return {
            "00_config": base / "00_config",
            "01_querypacks": base / "01_querypacks",
            "02_metadata": base / "02_metadata",
            "03A_metadata_hits": base / "03_corpus" / "03A_metadata_hits",
            "03B_public_downloads": base / "03_corpus" / "03B_public_downloads",
            "03C_official_docs": base / "03_corpus" / "03C_official_docs",
            "03D_manual_uploads": base / "03_corpus" / "03D_manual_uploads",
            "04_ocr_text": base / "04_ocr_text",
            "05_extraction": base / "05_extraction",
            "06_tables": base / "06_tables",
            "07_logs": base / "07_logs",
            "08_docs": base / "08_docs",
            "09_global_watch": base / "09_global_watch",
            "10_curated": base / "10_curated",
        }

def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
