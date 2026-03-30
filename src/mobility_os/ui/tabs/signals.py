from __future__ import annotations

import json
import pandas as pd
import streamlit as st

from mobility_os.ui.charts import make_alert_level_chart, make_line
from mobility_os.ui.maps import build_hotspot_signals, render_signals_map
from mobility_os.ui.components import render_summary_table


def _json_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def render_signals_tab(df: pd.DataFrame, latest: dict, hotspots_df: pd.DataFrame, focus_name: str | None, window: int) -> None:
    st.markdown("## Signals & Alerts Map")
    if df.empty:
        st.info("No simulation data yet.")
        return
    signals_df = build_hotspot_signals(hotspots_df, df, latest, focus_name)
    if signals_df.empty:
        st.info("No signal layer available.")
        return
    active_hotspots = pd.DataFrame(_json_list(latest.get("active_hotspots_json")))
    impact_chain = pd.DataFrame(_json_list(latest.get("impact_chain_json")))
    left, right = st.columns([1.8, 1.0])
    with left:
        render_signals_map(signals_df, height=760)
    with right:
        top_alerts = signals_df.sort_values(["severity", "name"], ascending=[False, True]).head(6).copy()
        top_alerts["severity"] = top_alerts["severity"].round(3)
        render_summary_table([
            ("Scenario", latest.get("scenario", "—")),
            ("Active event", latest.get("active_event", "none") or "none"),
            ("Focused hotspot", focus_name or "—"),
            ("Primary route", latest.get("decision_route", "—")),
            ("Active hotspots", int(latest.get("hotspot_count", len(active_hotspots) or 0))),
            ("Cascade score", round(float(latest.get("network_cascade_score", 0.0) or 0.0), 3)),
        ], "Operational context")
        st.plotly_chart(make_alert_level_chart(signals_df), use_container_width=True, key=f"signals_alert_levels_{latest.get('step_id',0)}")
        st.dataframe(top_alerts[["name", "alert_level", "phase", "signal_type", "active_event", "severity"]], use_container_width=True, hide_index=True, height=220)
        if not active_hotspots.empty:
            show = active_hotspots.copy()
            if "impacted_subsystems" in show.columns:
                show["impacted_subsystems"] = show["impacted_subsystems"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
            st.caption("Propagated hotspots")
            st.dataframe(show[["name", "severity", "depth", "impacted_subsystems"]].head(6), use_container_width=True, hide_index=True, height=210)
        if not impact_chain.empty:
            st.caption("Impact chain")
            st.dataframe(impact_chain[["from_hotspot", "to_hotspot", "transferred_severity"]].head(6), use_container_width=True, hide_index=True, height=190)
    live_df = df.tail(int(window))
    info_cols = st.columns(3)
    with info_cols[0]:
        st.plotly_chart(make_line(live_df, ["risk_score", "near_miss_index"], "Risk signal trend"), use_container_width=True, key=f"signals_risk_{latest.get('step_id',0)}")
    with info_cols[1]:
        st.plotly_chart(make_line(live_df, ["bus_bunching_index", "corridor_reliability_index"], "Transit signal trend"), use_container_width=True, key=f"signals_transit_{latest.get('step_id',0)}")
    with info_cols[2]:
        st.plotly_chart(make_line(live_df, ["curb_occupancy_rate", "illegal_curb_occupancy_rate", "gateway_delay_index"], "Curb / gateway trend"), use_container_width=True, key=f"signals_curb_{latest.get('step_id',0)}")
