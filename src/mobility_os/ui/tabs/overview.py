from __future__ import annotations

import pandas as pd
import streamlit as st

from mobility_os.ui.charts import make_line, make_route_mix_chart, make_subsystem_score_chart
from mobility_os.ui.components import chart_key, render_chip_row, render_section_header
from mobility_os.ui.maps import render_city_map, render_hotspot_summary


def render_overview_tab(df: pd.DataFrame, latest: dict, spec, hotspots_df: pd.DataFrame, focus_name: str | None, window: int, layer_filter: list[str]) -> None:
    render_section_header(
        "Operational Overview",
        "A compact view of the current hotspot, route choice and short-term urban dynamics.",
    )
    if df.empty:
        st.info("No simulation data yet.")
        return

    live_df = df.tail(int(window)).copy()

    top = st.columns([1.6, 1.0], gap="large")
    with top[0]:
        render_city_map(hotspots_df, latest, layer_filter=layer_filter, focused_name=focus_name, height=560)
    with top[1]:
        render_hotspot_summary(focus_name, hotspots_df, latest.get("scenario_note"), title="Focused hotspot")
        render_chip_row([
            (f"Scenario · {spec.title}", "neutral"),
            (f"Complexity · {spec.complexity}", "warn"),
            (f"Event · {latest.get('active_event') or 'none'}", "alert" if latest.get("active_event") else "dim"),
            (f"Route · {latest.get('decision_route', '—')}", "good"),
        ])
        st.plotly_chart(
            make_route_mix_chart(df.tail(max(int(window), 12))),
            use_container_width=True,
            key=chart_key("overview", "route_mix", latest),
        )

    render_section_header("Dynamics", "Short-window trends by subsystem.")
    row = st.columns(3, gap="large")
    with row[0]:
        st.plotly_chart(
            make_line(live_df, ["network_speed_index", "corridor_reliability_index"], "Network dynamics"),
            use_container_width=True,
            key=chart_key("overview", "network_dynamics", latest),
        )
    with row[1]:
        st.plotly_chart(
            make_line(live_df, ["bus_bunching_index", "bus_commercial_speed_kmh"], "Transit dynamics"),
            use_container_width=True,
            key=chart_key("overview", "transit_dynamics", latest),
        )
    with row[2]:
        st.plotly_chart(
            make_line(live_df, ["risk_score", "gateway_delay_index", "curb_occupancy_rate"], "Pressure dynamics"),
            use_container_width=True,
            key=chart_key("overview", "pressure_dynamics", latest),
        )

    render_section_header("Subsystem balance", "Live relative health of the main mobility domains.")
    st.plotly_chart(
        make_subsystem_score_chart(latest),
        use_container_width=True,
        key=chart_key("overview", "subsystem_score", latest),
    )
