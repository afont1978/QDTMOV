from __future__ import annotations

import streamlit as st

from mobility_os.runtime.live_ops import live_status_payload, should_auto_pause, step_many
from mobility_os.runtime.runtime import MobilityRuntime
from mobility_os.scenarios.loader import load_scenarios
from mobility_os.io.hotspot_repo import load_hotspots
from mobility_os.ui.components import inject_global_styles, render_hero, render_kpi_row, render_status_bar
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
    ss.setdefault("refresh_s", 1.0)
    ss.setdefault("auto_pause_critical", True)
    ss.setdefault("map_layers", list(LAYER_COLORS.keys()))
    ss.setdefault("focus_hotspot_mode", "Auto (scenario hotspot)")
    ss.setdefault("twin_sel", "intersection")
    ss.setdefault("rt", MobilityRuntime(ss["scenario"], ss["seed"]))
    ss.setdefault("live_notice", "")


def _rebuild() -> None:
    st.session_state["rt"] = MobilityRuntime(st.session_state["scenario"], st.session_state["seed"])
    st.session_state["running"] = False
    st.session_state["live_notice"] = ""


def render_app() -> None:
    st.set_page_config(page_title="Barcelona Mobility Control Room", layout="wide")

    _ensure_state()
    inject_global_styles()

    ss = st.session_state
    scenarios = load_scenarios()
    hotspots = load_hotspots()
    hotspots_df = hotspots_dataframe(hotspots)

    render_hero(
        "Barcelona Mobility Control Room",
        "Live synthetic control room with storyboard, executive dashboard, signals, what-if simulation, twins, audit and explainability.",
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
        new_seed = st.number_input("Seed", min_value=1, max_value=999999, value=int(ss["seed"]), step=1)

        if st.button("Apply", use_container_width=True):
            ss["scenario"] = new_scenario
            ss["seed"] = int(new_seed)
            _rebuild()
            st.rerun()

        cols = st.columns(3)
        with cols[0]:
            if st.button("Start", use_container_width=True):
                ss["running"] = True
                ss["live_notice"] = ""
                st.rerun()
        with cols[1]:
            if st.button("Pause", use_container_width=True):
                ss["running"] = False
                st.rerun()
        with cols[2]:
            if st.button("Reset", use_container_width=True):
                _rebuild()
                st.rerun()

        cols2 = st.columns(2)
        with cols2[0]:
            if st.button("Run 10 steps", use_container_width=True):
                step_many(ss["rt"], 10)
                st.rerun()
        with cols2[1]:
            if st.button("Run 50 steps", use_container_width=True):
                step_many(ss["rt"], 50)
                st.rerun()

        if st.button("Step", use_container_width=True):
            ss["rt"].step()
            st.rerun()

        ss["refresh_s"] = st.slider("Live refresh interval (s)", 0.5, 2.0, float(ss["refresh_s"]), step=0.1)
        ss["window"] = st.slider("Visible window", 12, 120, int(ss["window"]), step=6)
        ss["auto_pause_critical"] = st.checkbox("Auto-pause on critical state", value=bool(ss["auto_pause_critical"]))

        ss["map_layers"] = st.multiselect(
            "Visible map layers",
            options=list(LAYER_COLORS.keys()),
            default=ss.get("map_layers", list(LAYER_COLORS.keys())),
        )

        hotspot_options = ["Auto (scenario hotspot)"] + ([] if hotspots_df.empty else hotspots_df["name"].tolist())
        default_focus = ss.get("focus_hotspot_mode", "Auto (scenario hotspot)")
        default_index = hotspot_options.index(default_focus) if default_focus in hotspot_options else 0
        ss["focus_hotspot_mode"] = st.selectbox("Focus hotspot", hotspot_options, index=default_index)

    run_every = f"{ss['refresh_s']}s" if ss.get("running", False) else None

    @st.fragment(run_every=run_every)
    def render_live_content() -> None:
        if st.session_state.get("running", False):
            st.session_state["rt"].step()

        df = st.session_state["rt"].dataframe()
        latest = {} if df.empty else df.iloc[-1].to_dict()

        if st.session_state.get("auto_pause_critical", True):
            pause, message = should_auto_pause(latest)
            if pause and st.session_state.get("running", False):
                st.session_state["running"] = False
                st.session_state["live_notice"] = message

        current_scenario = st.session_state["scenario"]
        spec = scenarios[current_scenario]
        focus_name = selected_hotspot_name(
            latest,
            st.session_state.get("focus_hotspot_mode", "Auto (scenario hotspot)"),
        )

        status = live_status_payload(df, latest, st.session_state.get("running", False))
        render_status_bar([
            ("Running", "Yes" if status["running"] else "No"),
            ("Steps", status["steps"]),
            ("Event", status["event"]),
            ("Route", status["route"]),
            ("Hotspot", status["hotspot"]),
        ])

        if st.session_state.get("live_notice"):
            st.warning(st.session_state["live_notice"])

        render_kpi_row([
            ("Route", latest.get("decision_route", "—"), latest.get("route_reason", "")),
            ("Network speed", f'{latest.get("network_speed_index", 0):.2f}', "Current network flow quality"),
            ("Bus bunching", f'{latest.get("bus_bunching_index", 0):.2f}', "Service stability proxy"),
            ("Risk", f'{latest.get("risk_score", 0):.2f}', "Safety pressure indicator"),
            ("Gateway delay", f'{latest.get("gateway_delay_index", 0):.2f}', "Access pressure indicator"),
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
