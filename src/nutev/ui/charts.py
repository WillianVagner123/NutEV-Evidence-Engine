from __future__ import annotations

import pandas as pd


def value_counts_df(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if df.empty or col not in df.columns:
        return pd.DataFrame(columns=[col, 'count'])
    out = df[col].astype(str).value_counts(dropna=False).reset_index()
    out.columns = [col, 'count']
    return out
