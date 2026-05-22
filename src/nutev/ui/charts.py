from __future__ import annotations

import pandas as pd
import streamlit as st


def value_counts_df(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if df.empty or col not in df.columns:
        return pd.DataFrame(columns=[col, "count"])
    out = df[col].astype(str).value_counts(dropna=False).reset_index()
    out.columns = [col, "count"]
    return out


def render_bar_chart(df: pd.DataFrame, col: str, title: str) -> None:
    counts = value_counts_df(df, col)
    st.subheader(title)
    if counts.empty:
        st.caption("not available yet")
        return
    st.bar_chart(counts.set_index(col))


def render_status_distribution(df: pd.DataFrame, status_col: str) -> None:
    render_bar_chart(df, status_col, f"{status_col} distribution")


def render_pipeline_timeline(events: pd.DataFrame) -> None:
    st.subheader("Pipeline timeline")
    if events.empty:
        st.caption("not available yet")
        return
    cols = [c for c in ["event_at", "stage", "event_kind", "event_type", "message"] if c in events.columns]
    st.dataframe(events[cols].tail(100), use_container_width=True)


def render_domain_distribution(df: pd.DataFrame) -> None:
    for col in ["nutev_domains", "domains", "domain"]:
        if col in df.columns:
            render_bar_chart(df, col, "Domain distribution")
            return
    st.caption("Domain distribution not available yet")


def render_recommendation_status_chart(df: pd.DataFrame) -> None:
    render_status_distribution(df, "recommendation_status")
