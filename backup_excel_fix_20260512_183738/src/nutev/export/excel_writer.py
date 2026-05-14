from __future__ import annotations
from pathlib import Path
import pandas as pd

def write_analysis_xlsx(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_excel(path, index=False)
