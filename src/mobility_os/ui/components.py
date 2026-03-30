from __future__ import annotations

from typing import Any, Iterable, Tuple

import pandas as pd
import streamlit as st


def render_kpi_row(items: Iterable[tuple[str, Any]]) -> None:
    items = list(items)
    cols = st.columns(len(items)) if items else []
    for col, (label, value) in zip(cols, items):
        col.metric(label, value)


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


def chart_key(tab: str, name: str, latest: dict | None = None, suffix: str | int | None = None) -> str:
    step = 0 if not latest else latest.get("step_id", 0)
    extra = "" if suffix is None else f"_{suffix}"
    return f"{tab}_{name}_{step}{extra}"
