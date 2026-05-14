from __future__ import annotations
from pathlib import Path

def extract_docx_text(path: Path) -> str:
    import docx
    d = docx.Document(str(path))
    return "\n".join(p.text for p in d.paragraphs if p.text)
