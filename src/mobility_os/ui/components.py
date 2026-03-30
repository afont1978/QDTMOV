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
            padding-top: 0.75rem;
            padding-bottom: 1.2rem;
        }
        .qdt-hero {
            padding: 1.15rem 1.2rem;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 22px;
            background:
                radial-gradient(circle at top left, rgba(48,72,117,0.90), rgba(12,18,28,0.98) 58%),
                linear-gradient(135deg, rgba(15,23,42,0.96), rgba(17,24,39,0.96));
            box-shadow: 0 12px 28px rgba(0,0,0,0.28);
            margin-bottom: 0.9rem;
        }
        .qdt-hero-title {
            font-size: 2.0rem;
            font-weight: 760;
            line-height: 1.08;
            color: #f8fafc;
            margin-bottom: 0.2rem;
            letter-spacing: 0.01em;
        }
        .qdt-hero-subtitle {
            font-size: 0.98rem;
            color: #cbd5e1;
            line-height: 1.45;
            max-width: 1024px;
        }
        .qdt-section {
            margin: 0.4rem 0 0.75rem 0;
        }
        .qdt-section-title {
            font-size: 1.08rem;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 0.12rem;
        }
        .qdt-section-subtitle {
            font-size: 0.88rem;
            color: #94a3b8;
            line-height: 1.4;
            margin-bottom: 0.35rem;
        }
        .qdt-status {
            display:flex;
            gap:0.5rem;
            flex-wrap:wrap;
            margin:0.15rem 0 0.9rem 0;
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
        .qdt-kpi-grid {
            display:grid;
            grid-template-columns:repeat(5, minmax(0, 1fr));
            gap:0.65rem;
            margin:0.2rem 0 1rem 0;
        }
        .qdt-kpi-card {
            padding:0.78rem 0.85rem;
            border-radius:18px;
            border:1px solid rgba(255,255,255,0.07);
            background:linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
            min-height:94px;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
        }
        .qdt-kpi-label {
            font-size:0.74rem;
            text-transform:uppercase;
            letter-spacing:0.08em;
            color:#94a3b8;
            margin-bottom:0.45rem;
        }
        .qdt-kpi-value {
            font-size:1.45rem;
            font-weight:760;
            color:#f8fafc;
            line-height:1.1;
        }
        .qdt-kpi-note {
            font-size:0.80rem;
            color:#cbd5e1;
            margin-top:0.36rem;
            line-height:1.3;
        }
        .qdt-panel {
            padding:0.82rem 0.95rem;
            border-radius:18px;
            border:1px solid rgba(255,255,255,0.06);
            background:rgba(255,255,255,0.025);
            margin-bottom:0.8rem;
        }
        .qdt-panel-title {
            font-size:0.82rem;
            text-transform:uppercase;
            letter-spacing:0.08em;
            color:#94a3b8;
            margin-bottom:0.55rem;
        }
        .qdt-divider {
            height:1px;
            background:linear-gradient(90deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02));
            margin:0.8rem 0 1rem 0;
        }
        div[data-testid="stDataFrame"] div[role="table"] {
            border-radius: 14px;
            overflow: hidden;
        }
        @media (max-width: 1100px) {
            .qdt-kpi-grid { grid-template-columns:repeat(2, minmax(0,1fr)); }
        }
        @media (max-width: 680px) {
            .qdt-kpi-grid { grid-template-columns:repeat(1, minmax(0,1fr)); }
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


def render_section_header(title: str, subtitle: str | None = None) -> None:
    subtitle_html = f'<div class="qdt-section-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div class="qdt-section">
          <div class="qdt-section-title">{title}</div>
          {subtitle_html}
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
    cards = []
    for item in items:
        if len(item) == 2:
            label, value = item
            note = ""
        elif len(item) == 3:
            label, value, note = item
        else:
            continue
        note_html = f'<div class="qdt-kpi-note">{note}</div>' if note else ""
        cards.append(
            f"""
            <div class="qdt-kpi-card">
              <div class="qdt-kpi-label">{label}</div>
              <div class="qdt-kpi-value">{value}</div>
              {note_html}
            </div>
            """
        )
    st.markdown(f'<div class="qdt-kpi-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_panel_start(title: str) -> None:
    st.markdown(
        f"""
        <div class="qdt-panel">
          <div class="qdt-panel-title">{title}</div>
        """,
        unsafe_allow_html=True,
    )


def render_panel_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_divider() -> None:
    st.markdown('<div class="qdt-divider"></div>', unsafe_allow_html=True)


def render_summary_table(rows: list[tuple[str, Any]], title: str | None = None) -> None:
    if title:
        render_section_header(title)
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
