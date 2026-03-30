from __future__ import annotations

from typing import Any, Iterable, Tuple

import pandas as pd
import streamlit as st


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1680px;
            padding-top: 0.85rem;
            padding-bottom: 1.3rem;
        }
        .qdt-hero {
            padding: 1.05rem 1.2rem;
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 22px;
            background: radial-gradient(circle at top left, rgba(38,53,83,0.96), rgba(11,16,26,0.98) 60%);
            margin-bottom: 1rem;
            box-shadow: 0 12px 28px rgba(0,0,0,0.25);
        }
        .qdt-hero-title {
            font-size: 2rem;
            font-weight: 750;
            color: #F4F7FB;
            margin-bottom: 0.15rem;
            letter-spacing: 0.01em;
        }
        .qdt-hero-subtitle {
            font-size: 0.98rem;
            color: #C9D4E3;
            line-height: 1.4;
        }
        .qdt-status {
            display:flex;
            gap:0.55rem;
            flex-wrap:wrap;
            margin:0.35rem 0 1rem 0;
        }
        .qdt-chip {
            display:inline-flex;
            align-items:center;
            gap:0.35rem;
            padding:0.28rem 0.62rem;
            border-radius:999px;
            font-size:0.78rem;
            font-weight:600;
            border:1px solid rgba(255,255,255,0.08);
        }
        .qdt-card {
            padding: 0.85rem 1rem;
            border-radius: 18px;
            background: rgba(255,255,255,0.028);
            border: 1px solid rgba(255,255,255,0.06);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
        }
        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(255,255,255,0.038), rgba(255,255,255,0.02));
            border: 1px solid rgba(255,255,255,0.07);
            padding: 0.6rem 0.8rem;
            border-radius: 16px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="qdt-hero">
          <div class="qdt-hero-title">{title}</div>
          <div class="qdt-hero-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_bar(items: Iterable[tuple]) -> None:
    tone_map = {
        "neutral": ("rgba(94,138,196,0.16)", "#dbe8ff"),
        "warn": ("rgba(255,193,7,0.16)", "#fff3cc"),
        "alert": ("rgba(244,67,54,0.16)", "#ffdede"),
        "good": ("rgba(76,175,80,0.16)", "#e6ffe8"),
        "dim": ("rgba(255,255,255,0.06)", "#d0dae6"),
    }
    chips = []
    for item in items:
        if len(item) == 2:
            label, value = item
            tone = "neutral"
        elif len(item) == 3:
            label, value, tone = item
        else:
            continue
        bg, fg = tone_map.get(tone, tone_map["neutral"])
        chips.append(
            f'<span class="qdt-chip" style="background:{bg};color:{fg};">{label}: {value}</span>'
        )
    st.markdown(f'<div class="qdt-status">{"".join(chips)}</div>', unsafe_allow_html=True)


def render_kpi_row(items: Iterable[tuple]) -> None:
    items = list(items)
    cols = st.columns(len(items)) if items else []
    for col, item in zip(cols, items):
        if len(item) == 2:
            label, value = item
            delta = None
        elif len(item) == 3:
            label, value, delta = item
        else:
            continue
        col.metric(label, value, delta)


def render_summary_table(rows: list[tuple[str, Any]], title: str | None = None) -> None:
    if title:
        st.subheader(title)
    df = pd.DataFrame([{"Field": k, "Value": v} for k, v in rows])
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_chip_row(items: Iterable[Tuple[str, str]]) -> None:
    tone_map = {
        "neutral": ("rgba(94,138,196,0.16)", "#dbe8ff"),
        "warn": ("rgba(255,193,7,0.16)", "#fff3cc"),
        "alert": ("rgba(244,67,54,0.16)", "#ffdede"),
        "good": ("rgba(76,175,80,0.16)", "#e6ffe8"),
        "dim": ("rgba(255,255,255,0.06)", "#d0dae6"),
    }
    html_items = []
    for text, tone in items:
        bg, fg = tone_map.get(tone, tone_map["neutral"])
        html_items.append(
            f'<span class="qdt-chip" style="background:{bg};color:{fg};margin-right:0.35rem;margin-bottom:0.35rem;">{text}</span>'
        )
    st.markdown("".join(html_items), unsafe_allow_html=True)


def chart_key(tab: str, name: str, latest: dict | None = None, suffix: str | int | None = None) -> str:
    step = 0 if not latest else latest.get("step_id", 0)
    extra = "" if suffix is None else f"_{suffix}"
    return f"{tab}_{name}_{step}{extra}"
