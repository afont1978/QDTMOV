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


def _safe_plotly_bar(df: pd.DataFrame, **kwargs):
    if df.empty:
        return None
    return px.bar(df, **kwargs)


def _build_trend_long(trends_df: pd.DataFrame) -> pd.DataFrame:
    if trends_df.empty or "Metric" not in trends_df.columns:
        return pd.DataFrame(columns=["Metric", "Window", "Value"])
    delta_cols = [c for c in trends_df.columns if c.startswith("Δ")]
    if not delta_cols:
        return pd.DataFrame(columns=["Metric", "Window", "Value"])
    long_df = trends_df.melt(
        id_vars=["Metric"],
        value_vars=delta_cols,
        var_name="Window",
        value_name="Value",
    )
    return long_df


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
    trends_long_df = _build_trend_long(trends_df)
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
        if not score_df.empty and {"Subsystem", "Score"}.issubset(score_df.columns):
            fig_scores = px.bar(
                score_df,
                x="Subsystem",
                y="Score",
                color="Subsystem",
                template="plotly_dark",
                title="Subsystem scores",
            )
            fig_scores.update_layout(height=320, margin=dict(l=20, r=20, t=50, b=20), showlegend=False)
            st.plotly_chart(fig_scores, use_container_width=True, key=chart_key("executive", "scores", latest))
        else:
            st.info("No subsystem score data available.")

    with charts[1]:
        if not pressure_df.empty and {"Pressure", "Value"}.issubset(pressure_df.columns):
            fig_pressure = px.bar(
                pressure_df,
                x="Value",
                y="Pressure",
                orientation="h",
                template="plotly_dark",
                title="Pressure ranking",
            )
            fig_pressure.update_layout(height=320, margin=dict(l=20, r=20, t=50, b=20), showlegend=False)
            st.plotly_chart(fig_pressure, use_container_width=True, key=chart_key("executive", "pressure", latest))
        else:
            st.info("No pressure ranking data available.")

    bottom = st.columns(2)
    with bottom[0]:
        if not routes_df.empty and {"Route", "Count"}.issubset(routes_df.columns):
            fig_routes = px.pie(
                routes_df,
                names="Route",
                values="Count",
                hole=0.55,
                template="plotly_dark",
                title="Route mix",
            )
            fig_routes.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_routes, use_container_width=True, key=chart_key("executive", "route_mix", latest))
        else:
            st.info("No route mix data available.")

    with bottom[1]:
        if not trends_long_df.empty and {"Metric", "Window", "Value"}.issubset(trends_long_df.columns):
            fig_trends = px.line(
                trends_long_df,
                x="Window",
                y="Value",
                color="Metric",
                template="plotly_dark",
                title="Rolling trend deltas",
                markers=True,
            )
            fig_trends.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_trends, use_container_width=True, key=chart_key("executive", "trends", latest))
        else:
            st.info("No trend data available.")

    status_rows = subsystem_status_rows(latest)
    status_df = pd.DataFrame(status_rows, columns=["Subsystem", "Status", "Score"])
    st.dataframe(status_df, use_container_width=True, hide_index=True)

    with st.expander("Trend table", expanded=False):
        st.dataframe(trends_df, use_container_width=True, hide_index=True)
