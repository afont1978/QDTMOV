from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from mobility_os.runtime.executive import (
    executive_snapshot,
    pressure_ranking_df,
    route_mix_df,
    subsystem_scores_df,
    subsystem_status_rows,
    trend_table,
)
from mobility_os.ui.components import render_chip_row, render_summary_table


STATUS_TONES = {
    "Green": "good",
    "Amber": "warn",
    "Red": "alert",
}


def render_executive_dashboard_tab(df: pd.DataFrame) -> None:
    st.markdown("## Executive Dashboard")
    if df.empty:
        st.info("No records available yet.")
        return

    latest = df.iloc[-1].to_dict()
    snapshot = executive_snapshot(df)
    score_df = subsystem_scores_df(latest)
    pressure_df = pressure_ranking_df(latest)
    trends_df = trend_table(df)
    routes_df = route_mix_df(df)

    top = st.columns(5)
    with top[0]:
        st.metric("City score", f"{snapshot['city_score']:.3f}")
    with top[1]:
        st.metric("Executive status", snapshot["city_status"])
    with top[2]:
        st.metric("Route", snapshot["route"])
    with top[3]:
        st.metric("Confidence", f"{snapshot['confidence']*100:.1f}%")
    with top[4]:
        st.metric("Latency", f"{snapshot['latency_ms']} ms")

    render_chip_row([
        (f"Scenario · {latest.get('scenario', '—')}", "neutral"),
        (f"Event · {snapshot['active_event']}", "alert" if snapshot['active_event'] != 'none' else "dim"),
        (f"Hotspot · {snapshot['hotspot']}", "warn"),
        (f"Fallback · {snapshot['fallback_triggered']}", "alert" if snapshot['fallback_triggered'] else "good"),
    ])

    summary = st.columns([1.0, 1.0])
    with summary[0]:
        render_summary_table([
            ("Scenario", latest.get("scenario", "—")),
            ("Mode", latest.get("mode", "—")),
            ("Primary hotspot", latest.get("primary_hotspot_name", "—")),
            ("Active event", latest.get("active_event", "none") or "none"),
            ("Route reason", latest.get("route_reason", "—")),
        ], "Executive summary")
    with summary[1]:
        rows = subsystem_status_rows(latest)
        render_summary_table([(name, f"{status} · {score:.3f}") for name, status, score in rows], "Subsystem status")

    charts = st.columns(2)
    with charts[0]:
        fig = px.bar(
            score_df,
            x="Score",
            y="Subsystem",
            orientation="h",
            template="plotly_dark",
            title="Subsystem scoreboard",
            range_x=[0, 1.05],
        )
        fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=340, showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key=f"executive_subsystem_{int(latest.get('step_id', 0) or 0)}")
    with charts[1]:
        fig = px.bar(
            pressure_df.head(6),
            x="Value",
            y="Pressure",
            orientation="h",
            template="plotly_dark",
            title="Pressure ranking",
            range_x=[0, 1.05],
        )
        fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=340, showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key=f"executive_pressure_{int(latest.get('step_id', 0) or 0)}")

    lower = st.columns(2)
    with lower[0]:
        trend_cols = [c for c in ["step_operational_score", "network_speed_index", "risk_score", "gateway_delay_index"] if c in df.columns]
        work = df[["step_id", *trend_cols]].tail(60).copy()
        long_df = work.melt(id_vars=["step_id"], var_name="Metric", value_name="Value")
        fig = px.line(long_df, x="step_id", y="Value", color="Metric", template="plotly_dark", title="Executive trend window")
        fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=340)
        st.plotly_chart(fig, use_container_width=True, key=f"executive_trend_{int(latest.get('step_id', 0) or 0)}")
    with lower[1]:
        if routes_df.empty:
            st.info("No route mix available yet.")
        else:
            fig = px.pie(routes_df, names="Route", values="Count", hole=0.55, template="plotly_dark", title="Route mix")
            fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=340)
            st.plotly_chart(fig, use_container_width=True, key=f"executive_routes_{int(latest.get('step_id', 0) or 0)}")

    st.markdown("### Window trends")
    st.dataframe(trends_df, use_container_width=True, hide_index=True, height=240)
