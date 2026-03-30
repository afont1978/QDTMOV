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
from mobility_os.ui.components import chart_key, render_chip_row, render_section_header, render_summary_table


def render_executive_dashboard_tab(df: pd.DataFrame) -> None:
    render_section_header(
        "Executive Dashboard",
        "Decision-oriented KPIs and subsystem balance for a quick situation appraisal.",
    )
    if df.empty:
        st.info("No records available yet.")
        return

    latest = df.iloc[-1].to_dict()
    snapshot = executive_snapshot(df)
    score_df = subsystem_scores_df(latest)
    pressure_df = pressure_ranking_df(latest)
    trends_df = trend_table(df)
    routes_df = route_mix_df(df)

    top = st.columns(5, gap="large")
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

    summary = st.columns([1.0, 1.0], gap="large")
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
        ], "Operational picture")

    render_section_header("Subsystem and pressure view", "Balance between performance, risk and operational stress.")
    lower = st.columns([1.05, 1.0, 0.95], gap="large")
    with lower[0]:
        fig_scores = px.bar(score_df, x="Score", y="Subsystem", orientation="h", template="plotly_dark", title="Subsystem scores")
        fig_scores.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=320, showlegend=False, xaxis_range=[0, 1.05])
        st.plotly_chart(fig_scores, use_container_width=True, key=chart_key("executive", "subsystem_scores", latest))
    with lower[1]:
        if not pressure_df.empty and {"Pressure", "Value"}.issubset(pressure_df.columns):
            fig_pressure = px.bar(
                pressure_df,
                x="Value",
                y="Pressure",
                orientation="h",
                template="plotly_dark",
                title="Pressure ranking",
            )
            fig_pressure.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=320, showlegend=False)
            st.plotly_chart(fig_pressure, use_container_width=True, key=chart_key("executive", "pressure_ranking", latest))
        else:
            st.info("Pressure ranking not available.")
    with lower[2]:
        if not routes_df.empty and {"Route", "Count"}.issubset(routes_df.columns):
            fig_routes = px.pie(
                routes_df,
                names="Route",
                values="Count",
                hole=0.55,
                template="plotly_dark",
                title="Route mix",
            )
            fig_routes.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=320)
            st.plotly_chart(fig_routes, use_container_width=True, key=chart_key("executive", "route_mix", latest))
        else:
            st.info("Route mix not available.")

    render_section_header("Trends and status", "Short executive deltas and current subsystem condition.")
    bottom = st.columns([1.15, 0.95], gap="large")
    with bottom[0]:
        if not trends_df.empty and {"Metric", "Current", "Δ15", "Δ30", "Δ60"}.issubset(trends_df.columns):
            st.dataframe(trends_df, use_container_width=True, hide_index=True, height=320)
        else:
            st.info("Trend summary not available.")
    with bottom[1]:
        status_rows = subsystem_status_rows(latest)
        status_df = pd.DataFrame(status_rows)
        st.dataframe(status_df, use_container_width=True, hide_index=True, height=320)
