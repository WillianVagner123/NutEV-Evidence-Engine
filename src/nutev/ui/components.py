from __future__ import annotations

import pandas as pd


def safe_columns(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    existing = [c for c in cols if c in df.columns]
    return df[existing].copy() if existing else pd.DataFrame()
