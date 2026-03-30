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
from mobility_os.ui.components import chart_key, render_chip_row, render_summary_table


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
            ("Decision route", latest.get("decision_route", "—")),
        ], "Current executive summary")
    with summary[1]:
        render_summary_table([
            ("Operational score", f"{latest.get('step_operational_score', 0.0):.3f}"),
            ("Network speed index", f"{latest.get('network_speed_index', 0.0):.3f}"),
            ("Bus bunching index", f"{latest.get('bus_bunching_index', 0.0):.3f}"),
            ("Risk score", f"{latest.get('risk_score', 0.0):.3f}"),
            ("Gateway delay index", f"{latest.get('gateway_delay_index', 0.0):.3f}"),
        ], "Current KPI state")

    charts = st.columns(2)
    with charts[0]:
        fig_scores = px.bar(score_df, x="Subsystem", y="Score", color="Subsystem", template="plotly_dark", title="Subsystem scores")
        fig_scores.update_layout(height=320, margin=dict(l=20, r=20, t=50, b=20), showlegend=False)
        st.plotly_chart(fig_scores, use_container_width=True, key=chart_key("executive", "scores", latest))
    with charts[1]:
        fig_pressure = px.bar(pressure_df, x="Pressure", y="Domain", orientation="h", template="plotly_dark", title="Pressure ranking")
        fig_pressure.update_layout(height=320, margin=dict(l=20, r=20, t=50, b=20), showlegend=False)
        st.plotly_chart(fig_pressure, use_container_width=True, key=chart_key("executive", "pressure", latest))

    bottom = st.columns(2)
    with bottom[0]:
        fig_routes = px.pie(routes_df, names="route", values="count", hole=0.55, template="plotly_dark", title="Route mix")
        fig_routes.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_routes, use_container_width=True, key=chart_key("executive", "route_mix", latest))
    with bottom[1]:
        fig_trends = px.line(trends_df, x="Window", y="Value", color="Metric", template="plotly_dark", title="Rolling trend snapshot")
        fig_trends.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_trends, use_container_width=True, key=chart_key("executive", "trends", latest))

    st.dataframe(pd.DataFrame(subsystem_status_rows(latest)), use_container_width=True, hide_index=True)
