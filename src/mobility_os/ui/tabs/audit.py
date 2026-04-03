from __future__ import annotations

import json
from typing import Any

import pandas as pd
import streamlit as st

from mobility_os.ui.charts import make_line
from mobility_os.ui.components import chart_key, render_chip_row, render_section_header, render_summary_table
from mobility_os.ui.maps import render_hotspot_summary


def _safe_json_loads(value: Any) -> Any:
    if value is None:
        return {}
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, float) and pd.isna(value):
        return {}
    if not isinstance(value, (str, bytes, bytearray)):
        return {}
    if isinstance(value, str):
        text = value.strip()
        if text in {"", "nan", "None", "null"}:
            return {}
        try:
            return json.loads(text)
        except Exception:
            return {"raw": value}
    try:
        return json.loads(value)
    except Exception:
        return {"raw": str(value)}


def render_audit_tab(df: pd.DataFrame, hotspots_df: pd.DataFrame) -> None:
    render_section_header(
        "Audit & Orchestration",
        "Inspect individual execution records, local time windows and technical decision traces.",
    )
    if df.empty:
        st.info("No records yet.")
        return

    cols_to_show = [
        "step_id",
        "ts",
        "mode",
        "scenario",
        "active_event",
        "primary_hotspot_name",
        "decision_route",
        "exec_ms",
        "decision_confidence",
        "step_operational_score",
        "fallback_triggered",
    ]
    cols_to_show = [c for c in cols_to_show if c in df.columns]
    st.dataframe(df[cols_to_show].tail(60), use_container_width=True, height=260)

    idx = st.number_input(
        "Record index (0-based)",
        min_value=0,
        max_value=max(0, len(df) - 1),
        value=max(0, len(df) - 1),
        step=1,
    )
    row = df.iloc[int(idx)]

    lo = max(0, int(idx) - 8)
    hi = min(len(df), int(idx) + 9)
    window_df = df.iloc[lo:hi].copy()

    top = st.columns(4)
    with top[0]:
        st.metric("Route", str(row.get("decision_route", "—")))
    with top[1]:
        st.metric("Latency", f"{int(row.get('exec_ms', 0) or 0)} ms")
    with top[2]:
        conf = float(row.get("decision_confidence", 0.0) or 0.0) * 100.0
        st.metric("Confidence", f"{conf:.1f}%")
    with top[3]:
        score = float(row.get("step_operational_score", 0.0) or 0.0)
        st.metric("Score", f"{score:.3f}")

    render_chip_row([
        (f"Situation · {row.get('situation_type', '—')}", "neutral"),
        (f"Subproblem · {row.get('subproblem_type', '—')}", "warn"),
        (
            f"Action priority · {row.get('action_priority', '—')}",
            "alert" if str(row.get("action_priority", "")).lower() == "high" else "warn",
        ),
    ])

    g1, g2, g3 = st.columns(3)
    with g1:
        st.plotly_chart(
            make_line(window_df, ["network_speed_index", "corridor_reliability_index"], "Local urban performance"),
            use_container_width=True,
            key=chart_key("audit", "urban_performance", row.to_dict(), suffix=int(idx)),
        )
    with g2:
        st.plotly_chart(
            make_line(window_df, ["risk_score", "near_miss_index", "pedestrian_exposure"], "Local risk window"),
            use_container_width=True,
            key=chart_key("audit", "risk_window", row.to_dict(), suffix=int(idx)),
        )
    with g3:
        st.plotly_chart(
            make_line(window_df, ["bus_bunching_index", "curb_occupancy_rate", "gateway_delay_index"], "Operational pressure window"),
            use_container_width=True,
            key=chart_key("audit", "pressure_window", row.to_dict(), suffix=int(idx)),
        )

    details = st.columns([1.05, 1.05, 0.9])
    with details[0]:
        render_summary_table([
            ("Step", int(row.get("step_id", 0) or 0)),
            ("Mode", row.get("mode", "—")),
            ("Scenario", row.get("scenario", "—")),
            ("Event", row.get("active_event", "none") or "none"),
            ("Hotspot", row.get("primary_hotspot_name", "—")),
        ], "Record")
    with details[1]:
        render_summary_table([
            ("Network speed", float(row.get("network_speed_index", 0.0) or 0.0)),
            ("Bus bunching", float(row.get("bus_bunching_index", 0.0) or 0.0)),
            ("Curb occupancy", float(row.get("curb_occupancy_rate", 0.0) or 0.0)),
            ("Risk", float(row.get("risk_score", 0.0) or 0.0)),
            ("Gateway delay", float(row.get("gateway_delay_index", 0.0) or 0.0)),
        ], "State vector")
    with details[2]:
        render_summary_table([
            ("Route", row.get("decision_route", "—")),
            ("Fallback", bool(row.get("fallback_triggered", False))),
            ("Reasons", ", ".join(row.get("fallback_reasons", []) or [])),
            ("Latency breach", bool(row.get("latency_breach", False))),
        ], "Decision")

    render_hotspot_summary(row.get("primary_hotspot_name"), hotspots_df, row.get("scenario_note"), title="Audit hotspot")

    with st.expander("Technical detail"):
        tech_cols = st.columns(2)
        with tech_cols[0]:
            st.markdown("### Dispatch")
            st.json(_safe_json_loads(row.get("dispatch_json")))
            st.markdown("### Objective breakdown")
            st.json(_safe_json_loads(row.get("objective_breakdown_json")))
        with tech_cols[1]:
            st.markdown("### Quantum Request Envelope")
            st.json(_safe_json_loads(row.get("qre_json")))
            st.markdown("### Quantum Result")
            st.json(_safe_json_loads(row.get("result_json")))
