from __future__ import annotations

import html
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


def _esc(value: object) -> str:
    """HTML-escape a value before interpolating it into ``unsafe_allow_html`` markup.

    Dashboard cards render claim/recommendation text, document ids and titles
    that originate from scraped web content and LLM output. Escaping prevents a
    crafted value (e.g. ``<img src=x onerror=...>``) from executing as stored
    XSS in the analyst's browser.
    """
    return html.escape(str(value), quote=True)


STATUS_COLORS = {
    "ok": "#167a52",
    "available": "#167a52",
    "supported": "#167a52",
    "approved": "#167a52",
    "protocol_ready": "#167a52",
    "ready_for_human_review": "#d9a441",
    "needs_human_review": "#d9a441",
    "needs_adjudication": "#d9822b",
    "insufficient_evidence": "#c2410c",
    "conflicting": "#b91c1c",
    "conflicting_evidence": "#b91c1c",
    "missing": "#64748b",
    "not available yet": "#64748b",
}


def inject_premium_css() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; padding-bottom: 3rem; }
        [data-testid="stSidebar"] { background: linear-gradient(180deg, #f5faf6 0%, #edf7ef 100%); }
        .nutev-hero { border:1px solid rgba(20,35,27,.10); border-radius:28px; padding:28px; background:linear-gradient(135deg, rgba(255,255,255,.96), rgba(239,248,240,.92)); box-shadow:0 20px 60px rgba(22,122,82,.10); margin-bottom:18px; }
        .nutev-title { font-size:42px; line-height:1; font-weight:850; letter-spacing:-.05em; margin:0; color:#14231b; }
        .nutev-subtitle { color:#167a52; font-weight:750; margin-top:8px; }
        .nutev-muted { color:#607064; line-height:1.65; }
        .metric-card { border:1px solid rgba(20,35,27,.10); border-radius:22px; padding:18px; background:rgba(255,255,255,.88); box-shadow:0 12px 34px rgba(20,35,27,.06); min-height:116px; }
        .metric-label { color:#607064; font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:.04em; }
        .metric-value { color:#14231b; font-size:34px; font-weight:850; letter-spacing:-.04em; margin-top:8px; }
        .metric-helper { color:#607064; font-size:13px; margin-top:4px; }
        .section-card { border:1px solid rgba(20,35,27,.10); border-radius:24px; padding:22px; background:rgba(255,255,255,.90); box-shadow:0 14px 42px rgba(20,35,27,.06); margin:14px 0; }
        .status-pill { display:inline-block; border-radius:999px; padding:6px 10px; color:white; font-size:12px; font-weight:800; }
        .nutev-banner { border-radius:18px; padding:14px 16px; border:1px solid rgba(20,35,27,.10); margin:12px 0; }
        .banner-warning { background:#fff7ed; color:#7c2d12; }
        .banner-success { background:#ecfdf5; color:#064e3b; }
        .banner-info { background:#eff6ff; color:#1e3a8a; }
        .empty-state { border:1px dashed rgba(20,35,27,.18); border-radius:22px; padding:28px; background:rgba(255,255,255,.60); color:#607064; text-align:center; }
        .mini-card { border:1px solid rgba(20,35,27,.10); border-radius:18px; padding:16px; background:white; margin:10px 0; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def safe_columns(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    existing = [c for c in cols if c in df.columns]
    return df[existing].copy() if existing else pd.DataFrame()


def render_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="nutev-hero">
          <div class="nutev-title">{_esc(title)}</div>
          <div class="nutev-subtitle">{_esc(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: Any, helper: str | None = None) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{_esc(label)}</div>
          <div class="metric-value">{_esc(value)}</div>
          <div class="metric-helper">{_esc(helper or '')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_pill(status: str) -> str:
    color = STATUS_COLORS.get(str(status), "#64748b")
    return f'<span class="status-pill" style="background:{color}">{_esc(status)}</span>'


def warning_banner(text: str) -> None:
    st.markdown(f'<div class="nutev-banner banner-warning">{_esc(text)}</div>', unsafe_allow_html=True)


def success_banner(text: str) -> None:
    st.markdown(f'<div class="nutev-banner banner-success">{_esc(text)}</div>', unsafe_allow_html=True)


def info_banner(text: str) -> None:
    st.markdown(f'<div class="nutev-banner banner-info">{_esc(text)}</div>', unsafe_allow_html=True)


def section_card(title: str, body: str) -> None:
    st.markdown(f'<div class="section-card"><h3>{_esc(title)}</h3><p class="nutev-muted">{_esc(body)}</p></div>', unsafe_allow_html=True)


def empty_state(title: str, message: str) -> None:
    st.markdown(f'<div class="empty-state"><h3>{_esc(title)}</h3><p>{_esc(message)}</p></div>', unsafe_allow_html=True)


def download_card(label: str, path: Path) -> None:
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    st.markdown(
        f'<div class="mini-card"><b>{_esc(label)}</b><br><span class="nutev-muted">{_esc(path.name)} - {"available" if exists else "missing"} - {size} bytes</span></div>',
        unsafe_allow_html=True,
    )
    if exists:
        st.download_button(f"Download {label}", path.read_bytes(), file_name=path.name)


def artifact_card(path: Path) -> None:
    download_card(path.name, path)


def recommendation_card(row: pd.Series | dict[str, Any]) -> None:
    data = dict(row)
    status = data.get("recommendation_status", "not available")
    st.markdown(
        f"""
        <div class="mini-card">
          <b>{_esc(data.get('recommendation_text', data.get('recommendation_id', 'Recommendation')))}</b><br>
          {status_pill(str(status))}<br>
          <span class="nutev-muted">Component: {_esc(data.get('protocol_component', 'not mapped'))}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def claim_card(row: pd.Series | dict[str, Any]) -> None:
    data = dict(row)
    status = data.get("claim_status", "not available")
    st.markdown(
        f"""
        <div class="mini-card">
          <b>{_esc(data.get('claim_text', data.get('claim_id', 'Claim')))}</b><br>
          {status_pill(str(status))}<br>
          <span class="nutev-muted">Document: {_esc(data.get('document_id', 'not available'))}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def safety_notice() -> None:
    warning_banner(
        "RecommendationCandidate não é recomendação final. Entrada no Protocolo NutEV requer evidência documental, claim auditável, qualidade da evidência, ausência de conflito não adjudicado e revisão humana."
    )
