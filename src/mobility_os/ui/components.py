from __future__ import annotations

from typing import Any, Iterable, Tuple

import pandas as pd
import streamlit as st


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1rem; padding-bottom: 1rem; max-width: 1600px;}
        .qdt-shell {
            padding: 1rem 1.15rem;
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.08);
            background: linear-gradient(135deg, rgba(17,24,39,0.95), rgba(15,23,42,0.92));
            box-shadow: 0 8px 24px rgba(0,0,0,0.22);
            margin-bottom: 0.9rem;
        }
        .qdt-hero-title {font-size: 1.65rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.1rem;}
        .qdt-hero-subtitle {font-size: 0.94rem; color: #cbd5e1; line-height: 1.45;}
        .qdt-status {
            display:flex; gap:0.45rem; flex-wrap:wrap; margin:0.15rem 0 0.8rem 0;
        }
        .qdt-badge {
            display:inline-flex; align-items:center; gap:0.35rem;
            padding:0.25rem 0.58rem; border-radius:999px;
            font-size:0.78rem; font-weight:600;
            border:1px solid rgba(255,255,255,0.08);
            color:#e2e8f0;
            background:rgba(255,255,255,0.04);
        }
        .qdt-card {
            padding: 0.7rem 0.85rem;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.07);
            background: rgba(255,255,255,0.025);
            min-height: 92px;
        }
        .qdt-card-label {font-size:0.76rem; text-transform:uppercase; letter-spacing:0.08em; color:#94a3b8;}
        .qdt-card-value {font-size:1.45rem; font-weight:700; color:#f8fafc; margin-top:0.2rem;}
        .qdt-card-note {font-size:0.82rem; color:#cbd5e1; margin-top:0.35rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="qdt-shell">
          <div class="qdt-hero-title">{title}</div>
          <div class="qdt-hero-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chart_key(tab: str, name: str, latest: dict | None = None) -> str:
    step = 0 if not latest else latest.get("step_id", 0)
    return f"{tab}_{name}_{step}"


def render_kpi_row(items: Iterable[tuple[str, Any, str | None]]) -> None:
    items = list(items)
    cols = st.columns(len(items)) if items else []
    for col, item in zip(cols, items):
        if len(item) == 2:
            label, value = item
            note = ""
        else:
            label, value, note = item
        with col:
            st.markdown(
                f"""
                <div class="qdt-card">
                  <div class="qdt-card-label">{label}</div>
                  <div class="qdt-card-value">{value}</div>
                  <div class="qdt-card-note">{note or "&nbsp;"}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_summary_table(rows: list[tuple[str, Any]], title: str | None = None) -> None:
    if title:
        st.subheader(title)
    df = pd.DataFrame([{"Field": k, "Value": v} for k, v in rows])
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_chip_row(items: Iterable[Tuple[str, str]]) -> None:
    html_items = []
    tone_map = {
        "neutral": "#3b82f6",
        "warn": "#f59e0b",
        "alert": "#ef4444",
        "good": "#22c55e",
        "dim": "#64748b",
    }
    for text, tone in items:
        color = tone_map.get(tone, tone_map["neutral"])
        html_items.append(
            f'<span style="display:inline-block;padding:0.22rem 0.55rem;margin:0 0.3rem 0.3rem 0;border-radius:999px;background:{color}22;border:1px solid {color}66;color:#e5eef8;font-size:0.78rem;">{text}</span>'
        )
    st.markdown("".join(html_items), unsafe_allow_html=True)


def render_status_bar(items: Iterable[tuple[str, Any]]) -> None:
    badges = []
    for label, value in items:
        badges.append(f'<span class="qdt-badge"><strong>{label}:</strong> {value}</span>')
    st.markdown('<div class="qdt-status">' + "".join(badges) + '</div>', unsafe_allow_html=True)
