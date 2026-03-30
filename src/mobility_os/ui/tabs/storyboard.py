from __future__ import annotations

import json
import pandas as pd
import streamlit as st

from mobility_os.ui.charts import make_story_disturbance_chart, make_story_event_track, make_subsystem_score_chart
from mobility_os.ui.components import render_chip_row, render_summary_table
from mobility_os.ui.maps import render_hotspot_summary


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


def render_storyboard_tab(df: pd.DataFrame, latest: dict, spec, hotspots_df: pd.DataFrame, focus_name: str | None) -> None:
    st.markdown("## Scenario Storyboard")
    if df.empty:
        st.info("No simulation data yet.")
        return

    active_hotspots = pd.DataFrame(_json_list(latest.get("active_hotspots_json")))
    impact_chain = pd.DataFrame(_json_list(latest.get("impact_chain_json")))

    top = st.columns([1.1, 0.9])
    with top[0]:
        render_summary_table([
            ("Scenario", spec.title),
            ("Mode", spec.mode),
            ("Complexity", spec.complexity),
            ("Active event", latest.get("active_event", "none") or "none"),
            ("Primary hotspot", latest.get("primary_hotspot_name", "—")),
            ("Focused hotspot", focus_name or "—"),
            ("Decision route", latest.get("decision_route", "—")),
            ("Active hotspots", int(latest.get("hotspot_count", len(active_hotspots) or 0))),
            ("Cascade score", round(float(latest.get("network_cascade_score", 0.0) or 0.0), 3)),
        ], "Scenario profile")
        render_chip_row([
            (f"Subproblems · {len(spec.expected_subproblems)}", "warn"),
            (f"Interventions · {len(spec.recommended_interventions)}", "alert"),
            (f"KPIs · {len(spec.kpis)}", "neutral"),
            (f"Propagation links · {len(impact_chain)}", "dim"),
        ])
        st.write(spec.note or "No scenario note available.")
    with top[1]:
        render_hotspot_summary(focus_name or latest.get("primary_hotspot_name"), hotspots_df, latest.get("scenario_note"), title="Scenario anchor")

    charts = st.columns(3)
    with charts[0]:
        st.plotly_chart(make_story_event_track(spec, latest.get("active_event"), int(latest.get("step_id", 0) or 0)), use_container_width=True, key=f"story_events_{latest.get('step_id',0)}")
    with charts[1]:
        st.plotly_chart(make_story_disturbance_chart(spec), use_container_width=True, key=f"story_dist_{latest.get('step_id',0)}")
    with charts[2]:
        st.plotly_chart(make_subsystem_score_chart(latest), use_container_width=True, key=f"story_subsystems_{latest.get('step_id',0)}")

    bottom = st.columns(4)
    with bottom[0]:
        st.subheader("Primary hotspots")
        for item in spec.primary_hotspots or []:
            st.caption(item)
    with bottom[1]:
        st.subheader("Expected subproblems")
        for item in spec.expected_subproblems or []:
            st.caption(str(item).replace("_", " ").title())
    with bottom[2]:
        st.subheader("Recommended interventions")
        for item in spec.recommended_interventions or []:
            st.caption(str(item).replace("_", " ").title())
    with bottom[3]:
        st.subheader("Impact chain")
        if impact_chain.empty:
            st.caption("No propagated impact chain detected.")
        else:
            for _, row in impact_chain.head(6).iterrows():
                st.caption(f"{row.get('from_hotspot')} → {row.get('to_hotspot')} ({float(row.get('transferred_severity',0)):.2f})")

    if not active_hotspots.empty:
        show = active_hotspots.copy()
        if "impacted_subsystems" in show.columns:
            show["impacted_subsystems"] = show["impacted_subsystems"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
        st.subheader("Active hotspots cluster")
        st.dataframe(show[["name", "severity", "depth", "event_type", "impacted_subsystems"]], use_container_width=True, hide_index=True, height=240)

    if spec.kpis:
        st.subheader("Scenario KPI watchlist")
        rows = [(str(k).replace("_", " ").title(), latest.get(k, "—")) for k in spec.kpis]
        render_summary_table(rows, None)
