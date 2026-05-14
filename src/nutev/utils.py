from __future__ import annotations
from pathlib import Path
import json

def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')

def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
