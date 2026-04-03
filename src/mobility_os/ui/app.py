from __future__ import annotations

import math
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


def _delta(current: float | int | None, previous: float | int | None, higher_is_better: bool = True) -> str:
    if current is None or previous is None:
        return "—"
    try:
        c = float(current)
        p = float(previous)
    except Exception:
        return "—"
    d = c - p
    if abs(d) < 1e-9:
        arrow = "→"
    else:
        improving = d > 0 if higher_is_better else d < 0
        arrow = "↑" if improving else "↓"
    return f"{arrow} {d:+.03f}"


def _bar(value: float | int | None, max_value: float = 1.0, width: int = 8) -> str:
    try:
        v = float(value)
    except Exception:
        return "—"
    if max_value <= 0:
        max_value = 1.0
    ratio = max(0.0, min(v / max_value, 1.0))
    filled = int(round(ratio * width))
    return "█" * filled + "░" * (width - filled)


def _sparkline(values: list[float | int | None]) -> str:
    chars = "▁▂▃▄▅▆▇█"
    seq: list[float] = []
    for v in values:
        try:
            fv = float(v)
            if not math.isnan(fv):
                seq.append(fv)
        except Exception:
            pass
    if not seq:
        return "—"
    lo, hi = min(seq), max(seq)
    if abs(hi - lo) < 1e-12:
        return chars[3] * min(len(seq), 10)
    out = []
    for v in seq[-10:]:
        idx = int(round((v - lo) / (hi - lo) * (len(chars) - 1)))
        idx = max(0, min(idx, len(chars) - 1))
        out.append(chars[idx])
    return "".join(out)


def _history(df, column: str, n: int = 10) -> list[float]:
    if column not in df.columns or df.empty:
        return []
    vals = df[column].tail(n).tolist()
    out = []
    for v in vals:
        try:
            out.append(float(v))
        except Exception:
            pass
    return out


def _get_prev(df):
    if len(df) < 2:
        return {}
    return df.iloc[-2].to_dict()


def _tone_from_threshold(value: float, good_max: float, warn_max: float) -> tuple[str, str]:
    if value <= good_max:
        return "GREEN", "#22c55e"
    if value <= warn_max:
        return "AMBER", "#f59e0b"
    return "RED", "#ef4444"


def _tone_from_inverse_threshold(value: float, good_min: float, warn_min: float) -> tuple[str, str]:
    if value >= good_min:
        return "GREEN", "#22c55e"
    if value >= warn_min:
        return "AMBER", "#f59e0b"
    return "RED", "#ef4444"


def _chip(label: str, value: str, color: str) -> str:
    return (
        f'<span style="display:inline-block;padding:0.28rem 0.62rem;margin:0 0.35rem 0.35rem 0;'
        f'border-radius:999px;background:{color}22;border:1px solid {color}66;color:#e5eef8;'
        f'font-size:0.78rem;font-weight:600;">{label}: {value}</span>'
    )


def _render_semantic_status(latest: dict) -> None:
    try:
        risk = float(latest.get("risk_score", 0.0) or 0.0)
        bunching = float(latest.get("bus_bunching_index", 0.0) or 0.0)
        gateway = float(latest.get("gateway_delay_index", 0.0) or 0.0)
        speed = float(latest.get("network_speed_index", 0.0) or 0.0)
        score = float(latest.get("step_operational_score", 0.0) or 0.0)
    except Exception:
        risk = bunching = gateway = 0.0
        speed = score = 0.0

    risk_lbl, risk_color = _tone_from_threshold(risk, 0.35, 0.60)
    bunch_lbl, bunch_color = _tone_from_threshold(bunching, 0.22, 0.42)
    gateway_lbl, gateway_color = _tone_from_threshold(gateway, 0.30, 0.55)
    speed_lbl, speed_color = _tone_from_inverse_threshold(speed, 0.85, 0.65)
    score_lbl, score_color = _tone_from_inverse_threshold(score, 0.70, 0.50)

    html = "".join([
        _chip("Network", speed_lbl, speed_color),
        _chip("Transit", bunch_lbl, bunch_color),
        _chip("Risk", risk_lbl, risk_color),
        _chip("Gateway", gateway_lbl, gateway_color),
        _chip("Ops score", score_lbl, score_color),
    ])
    st.markdown(html, unsafe_allow_html=True)


def _group_rows(df, latest: dict, prev: dict) -> tuple[list[tuple], list[tuple], list[tuple]]:
    performance = [
        (
            "Network speed",
            f"{float(latest.get('network_speed_index', 0.0) or 0.0):.2f}",
            f"{_delta(latest.get('network_speed_index'), prev.get('network_speed_index'), True)}  {_sparkline(_history(df, 'network_speed_index'))}",
        ),
        (
            "Reliability",
            f"{float(latest.get('corridor_reliability_index', 0.0) or 0.0):.2f}",
            f"{_delta(latest.get('corridor_reliability_index'), prev.get('corridor_reliability_index'), True)}  {_sparkline(_history(df, 'corridor_reliability_index'))}",
        ),
        (
            "Operational score",
            f"{float(latest.get('step_operational_score', 0.0) or 0.0):.3f}",
            f"{_delta(latest.get('step_operational_score'), prev.get('step_operational_score'), True)}  {_bar(latest.get('step_operational_score'), 1.0)}",
        ),
    ]

    risk_safety = [
        (
            "Bus bunching",
            f"{float(latest.get('bus_bunching_index', 0.0) or 0.0):.2f}",
            f"{_delta(latest.get('bus_bunching_index'), prev.get('bus_bunching_index'), False)}  {_sparkline(_history(df, 'bus_bunching_index'))}",
        ),
        (
            "Risk",
            f"{float(latest.get('risk_score', 0.0) or 0.0):.2f}",
            f"{_delta(latest.get('risk_score'), prev.get('risk_score'), False)}  {_sparkline(_history(df, 'risk_score'))}",
        ),
        (
            "Near-miss",
            f"{float(latest.get('near_miss_index', 0.0) or 0.0):.2f}",
            f"{_delta(latest.get('near_miss_index'), prev.get('near_miss_index'), False)}  {_sparkline(_history(df, 'near_miss_index'))}",
        ),
    ]

    access_control = [
        (
            "Gateway delay",
            f"{float(latest.get('gateway_delay_index', 0.0) or 0.0):.2f}",
            f"{_delta(latest.get('gateway_delay_index'), prev.get('gateway_delay_index'), False)}  {_sparkline(_history(df, 'gateway_delay_index'))}",
        ),
        (
            "Curb occupancy",
            f"{float(latest.get('curb_occupancy_rate', 0.0) or 0.0):.2f}",
            f"{_delta(latest.get('curb_occupancy_rate'), prev.get('curb_occupancy_rate'), False)}  {_sparkline(_history(df, 'curb_occupancy_rate'))}",
        ),
        (
            "Confidence",
            f"{float(latest.get('decision_confidence', 0.0) or 0.0) * 100:.1f}%",
            f"{_delta(float(latest.get('decision_confidence', 0.0) or 0.0) * 100.0, float(prev.get('decision_confidence', 0.0) or 0.0) * 100.0, True)}  {_bar(float(latest.get('decision_confidence', 0.0) or 0.0), 1.0)}",
        ),
    ]
    return performance, risk_safety, access_control


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
        prev = _get_prev(df)
        current_scenario = st.session_state["scenario"]
        spec = scenarios[current_scenario]
        focus_name = selected_hotspot_name(
            latest,
            st.session_state.get("focus_hotspot_mode", "Auto (scenario hotspot)"),
        )

        st.subheader("Live monitor")
        info_cols = st.columns(5)
        info_cols[0].metric("Route", latest.get("decision_route", "—"))
        info_cols[1].metric("Event", latest.get("active_event", "none") or "none")
        info_cols[2].metric("Hotspot", focus_name or latest.get("primary_hotspot_name", "—") or "—")
        info_cols[3].metric("Step", int(latest.get("step_id", 0) or 0))
        info_cols[4].metric("Fallback", "Yes" if latest.get("fallback_triggered", False) else "No")

        _render_semantic_status(latest)

        perf, safety, access = _group_rows(df, latest, prev)

        st.caption("Performance")
        render_kpi_row(perf)
        st.caption("Risk & Safety")
        render_kpi_row(safety)
        st.caption("Access & Control")
        render_kpi_row(access)

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
