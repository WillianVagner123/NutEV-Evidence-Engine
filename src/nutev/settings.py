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
        b=self.project_root
        return {
            "00_config": b/"00_config",
            "01_querypacks": b/"01_querypacks",
            "02_metadata": b/"02_metadata",
            "03A_metadata_hits": b/"03_corpus"/"03A_metadata_hits",
            "03B_public_downloads": b/"03_corpus"/"03B_public_downloads",
            "03C_official_docs": b/"03_corpus"/"03C_official_docs",
            "03D_manual_uploads": b/"03_corpus"/"03D_manual_uploads",
            "04_ocr_text": b/"04_ocr_text",
            "05_extraction": b/"05_extraction",
            "06_tables": b/"06_tables",
            "07_logs": b/"07_logs",
            "08_docs": b/"08_docs",
        }

def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
