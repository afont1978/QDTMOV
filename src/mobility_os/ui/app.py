from __future__ import annotations

import streamlit as st

from mobility_os.runtime.runtime import MobilityRuntime
from mobility_os.scenarios.loader import load_scenarios
from mobility_os.io.hotspot_repo import load_hotspots
from mobility_os.ui.components import (
    inject_global_styles,
    render_hero,
    render_kpi_row,
    render_section_header,
    render_status_bar,
)
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


VIEWS = [
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
]

FORM_HEAVY_VIEWS = {"What-if & Simulation", "Scenario Editor"}


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
    ss.setdefault("view_selector", "Overview")
    ss.setdefault("live_interval_s", 2)
    ss.setdefault("rt", MobilityRuntime(ss["scenario"], ss["seed"]))


def _rebuild() -> None:
    st.session_state["rt"] = MobilityRuntime(
        st.session_state["scenario"],
        st.session_state["seed"],
    )
    st.session_state["running"] = False


def _view_selector(label: str, options: list[str], key: str) -> str:
    current = st.session_state.get(key, options[0])
    if hasattr(st, "segmented_control"):
        return st.segmented_control(label, options, default=current, key=key)
    return st.radio(label, options, index=options.index(current) if current in options else 0, key=key, horizontal=True)


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
        "Synthetic city control room with live monitoring, executive KPIs, signals, storyboard, twins, what-if analysis and explainability.",
    )

    top = st.columns([1.2, 1.0])
    with top[0]:
        render_section_header(
            "Live Operations",
            "Use a single active view to reduce flicker and keep the focus on the operational storyline.",
        )
    with top[1]:
        view = _view_selector("Current view", VIEWS, "view_selector")

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

        batch_cols = st.columns(2)
        with batch_cols[0]:
            if st.button("Run 10", use_container_width=True):
                for _ in range(10):
                    ss["rt"].step()
                st.rerun()
        with batch_cols[1]:
            if st.button("Run 50", use_container_width=True):
                for _ in range(50):
                    ss["rt"].step()
                st.rerun()

        ss["live_interval_s"] = st.slider("Live refresh interval (s)", 2, 5, int(ss["live_interval_s"]), step=1)
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

    live_refresh_enabled = ss.get("running", False) and view not in FORM_HEAVY_VIEWS
    run_every = f"{int(ss['live_interval_s'])}s" if live_refresh_enabled else None

    if ss.get("running", False) and view in FORM_HEAVY_VIEWS:
        st.info("Auto-refresh is paused on this view to avoid form flicker. Use Pause, Step, Run 10 or Run 50.")

    @st.fragment(run_every=run_every)
    def render_live_content() -> None:
        if st.session_state.get("running", False) and view not in FORM_HEAVY_VIEWS:
            st.session_state["rt"].step()

        df = st.session_state["rt"].dataframe()
        latest = {} if df.empty else df.iloc[-1].to_dict()
        current_scenario = st.session_state["scenario"]
        spec = scenarios[current_scenario]
        focus_name = selected_hotspot_name(
            latest,
            st.session_state.get("focus_hotspot_mode", "Auto (scenario hotspot)"),
        )

        status = {
            "running": st.session_state.get("running", False),
            "step": int(latest.get("step_id", 0) or 0),
            "event": latest.get("active_event", "none") or "none",
            "route": latest.get("decision_route", "—"),
            "hotspot": focus_name or latest.get("primary_hotspot_name", "—") or "—",
        }

        render_status_bar([
            ("Running", "Yes" if status["running"] else "No", "good" if status["running"] else "dim"),
            ("Step", status["step"], "neutral"),
            ("Event", status["event"], "alert" if status["event"] not in [None, "", "none"] else "dim"),
            ("Route", status["route"], "warn"),
            ("Hotspot", status["hotspot"], "neutral"),
        ])

        render_kpi_row([
            ("Route", latest.get("decision_route", "—"), latest.get("route_reason", "")),
            ("Network speed", f'{latest.get("network_speed_index", 0):.2f}', "Higher is better"),
            ("Bus bunching", f'{latest.get("bus_bunching_index", 0):.2f}', "Lower is better"),
            ("Risk", f'{latest.get("risk_score", 0):.2f}', "Lower is better"),
            ("Gateway delay", f'{latest.get("gateway_delay_index", 0):.2f}', "Access pressure indicator"),
        ])

        if view == "Overview":
            render_overview_tab(
                df,
                latest,
                spec,
                hotspots_df,
                focus_name,
                int(st.session_state["window"]),
                st.session_state.get("map_layers", list(LAYER_COLORS.keys())),
            )
        elif view == "Executive Dashboard":
            render_executive_dashboard_tab(df)
        elif view == "Map & Layers":
            render_map_layers_tab(
                df,
                latest,
                hotspots_df,
                focus_name,
                st.session_state.get("map_layers", list(LAYER_COLORS.keys())),
            )
        elif view == "Signals & Alerts Map":
            render_signals_tab(
                df,
                latest,
                hotspots_df,
                focus_name,
                int(st.session_state["window"]),
            )
        elif view == "Scenario Storyboard":
            render_storyboard_tab(df, latest, spec, hotspots_df, focus_name)
        elif view == "Mobility Twins":
            render_twins_tab(
                df,
                latest,
                hotspots_df,
                st.session_state["rt"].twin_snapshot(),
                int(st.session_state["window"]),
            )
        elif view == "What-if & Simulation":
            render_simulation_tab(df, latest, hotspots_df, focus_name)
        elif view == "Audit & Orchestration":
            render_audit_tab(df, hotspots_df)
        elif view == "Explainability":
            render_explainability_tab(df)
        elif view == "Scenario Editor":
            render_scenario_editor_tab()

    render_live_content()
