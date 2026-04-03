from __future__ import annotations

import streamlit as st

from mobility_os.runtime.runtime import MobilityRuntime
from mobility_os.scenarios.loader import load_scenarios
from mobility_os.io.hotspot_repo import load_hotspots
from mobility_os.ui.components import render_kpi_row
from mobility_os.ui.maps import LAYER_COLORS, hotspots_dataframe, selected_hotspot_name
from mobility_os.ui.tabs import (
    render_audit_tab,
    render_map_layers_tab,
    render_overview_tab,
    render_scenario_editor_tab,
    render_executive_dashboard_tab,
    render_explainability_tab,
    render_signals_tab,
    render_simulation_tab,
    render_storyboard_tab,
    render_twins_tab,
)


def _ensure_state() -> None:
    ss = st.session_state
    scenarios = load_scenarios()
    ss.setdefault("scenario", "corridor_congestion")
    if ss["scenario"] not in scenarios:
        ss["scenario"] = next(iter(scenarios))
    ss.setdefault("seed", 42)
    ss.setdefault("running", False)
    ss.setdefault("window", 36)
    ss.setdefault("map_layers", list(LAYER_COLORS.keys()))
    ss.setdefault("focus_hotspot_mode", "Auto (scenario hotspot)")
    ss.setdefault("twin_sel", "intersection")
    ss.setdefault("rt", MobilityRuntime(ss["scenario"], ss["seed"]))


def _rebuild() -> None:
    st.session_state["rt"] = MobilityRuntime(
        st.session_state["scenario"],
        st.session_state["seed"],
    )
    st.session_state["running"] = False


def render_app() -> None:
    st.set_page_config(page_title="Barcelona Mobility Control Room", layout="wide")

    _ensure_state()
    ss = st.session_state
    scenarios = load_scenarios()
    hotspots = load_hotspots()
    hotspots_df = hotspots_dataframe(hotspots)

    st.title("Barcelona Mobility Control Room")
    st.caption(
        "Refactored modular control room with storyboard, what-if simulation, "
        "twins, audit, scenario editing and explainability."
    )

    with st.sidebar:
        st.subheader("Control panel")

        scenario_keys = list(scenarios.keys())
        if ss["scenario"] not in scenario_keys:
            ss["scenario"] = scenario_keys[0]

        new_scenario = st.selectbox(
            "Scenario",
            scenario_keys,
            index=scenario_keys.index(ss["scenario"]),
            format_func=lambda x: scenarios[x].title,
        )

        new_seed = st.number_input(
            "Seed",
            min_value=1,
            max_value=999999,
            value=int(ss["seed"]),
            step=1,
        )

        if st.button("Apply", use_container_width=True):
            ss["scenario"] = new_scenario
            ss["seed"] = int(new_seed)
            _rebuild()
            st.rerun()

        cols = st.columns(4)

        with cols[0]:
            if st.button("Start", use_container_width=True):
                ss["running"] = True
                st.rerun()

        with cols[1]:
            if st.button("Pause", use_container_width=True):
                ss["running"] = False
                st.rerun()

        with cols[2]:
            if st.button("Step", use_container_width=True):
                ss["rt"].step()
                st.rerun()

        with cols[3]:
            if st.button("Reset", use_container_width=True):
                _rebuild()
                st.rerun()

        ss["window"] = st.slider("Visible window", 12, 96, int(ss["window"]), step=6)

        ss["map_layers"] = st.multiselect(
            "Visible map layers",
            options=list(LAYER_COLORS.keys()),
            default=ss.get("map_layers", list(LAYER_COLORS.keys())),
        )

        hotspot_options = ["Auto (scenario hotspot)"] + (
            [] if hotspots_df.empty else hotspots_df["name"].tolist()
        )
        default_focus = ss.get("focus_hotspot_mode", "Auto (scenario hotspot)")
        default_index = hotspot_options.index(default_focus) if default_focus in hotspot_options else 0

        ss["focus_hotspot_mode"] = st.selectbox(
            "Focus hotspot",
            hotspot_options,
            index=default_index,
        )

        st.caption(f"Running: {'Yes' if ss.get('running', False) else 'No'}")

    run_every = "1s" if ss.get("running", False) else None

    @st.fragment(run_every=run_every)
    def render_live_content() -> None:
        if st.session_state.get("running", False):
            st.session_state["rt"].step()

        df = st.session_state["rt"].dataframe()
        latest = {} if df.empty else df.iloc[-1].to_dict()
        current_scenario = st.session_state["scenario"]
        spec = scenarios[current_scenario]
        focus_name = selected_hotspot_name(
            latest,
            st.session_state.get("focus_hotspot_mode", "Auto (scenario hotspot)"),
        )

        render_kpi_row([
            ("Route", latest.get("decision_route", "—")),
            ("Network speed", f'{latest.get("network_speed_index", 0):.2f}'),
            ("Bus bunching", f'{latest.get("bus_bunching_index", 0):.2f}'),
            ("Risk", f'{latest.get("risk_score", 0):.2f}'),
            ("Gateway delay", f'{latest.get("gateway_delay_index", 0):.2f}'),
        ])

        tabs = st.tabs([
            "Overview",
            "Executive Dashboard",
            "Map & Layers",
            "Signals & Alerts Map",
            "Scenario Storyboard",
            "Mobility Twins",
            "What-if & Simulation",
            "Audit & Orchestration",
            "Explainability",
            "Scenario Editor",
        ])

        with tabs[0]:
            render_overview_tab(
                df,
                latest,
                spec,
                hotspots_df,
                focus_name,
                int(st.session_state["window"]),
                st.session_state.get("map_layers", list(LAYER_COLORS.keys())),
            )

        with tabs[1]:
            render_executive_dashboard_tab(df)

        with tabs[2]:
            render_map_layers_tab(
                df,
                latest,
                hotspots_df,
                focus_name,
                st.session_state.get("map_layers", list(LAYER_COLORS.keys())),
            )

        with tabs[3]:
            render_signals_tab(
                df,
                latest,
                hotspots_df,
                focus_name,
                int(st.session_state["window"]),
            )

        with tabs[4]:
            render_storyboard_tab(df, latest, spec, hotspots_df, focus_name)

        with tabs[5]:
            render_twins_tab(
                df,
                latest,
                hotspots_df,
                st.session_state["rt"].twin_snapshot(),
                int(st.session_state["window"]),
            )

        with tabs[6]:
            render_simulation_tab(df, latest, hotspots_df, focus_name)

        with tabs[7]:
            render_audit_tab(df, hotspots_df)

        with tabs[8]:
            render_explainability_tab(df)

        with tabs[9]:
            render_scenario_editor_tab()

    render_live_content()
