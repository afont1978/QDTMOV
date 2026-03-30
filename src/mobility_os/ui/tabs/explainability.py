from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from mobility_os.runtime.explainability import (
    explain_route_decision,
    objective_breakdown_df,
    safe_json_loads,
    trigger_signals_df,
)
from mobility_os.ui.components import render_chip_row, render_summary_table


def render_explainability_tab(df: pd.DataFrame) -> None:
    st.markdown("## Explainability")
    if df.empty:
        st.info("No records available yet.")
        return

    idx = st.number_input(
        "Record index (0-based)",
        min_value=0,
        max_value=max(0, len(df) - 1),
        value=max(0, len(df) - 1),
        step=1,
        key="explainability_record_idx",
    )
    row = df.iloc[int(idx)].to_dict()
    explanation = explain_route_decision(row)

    top = st.columns(4)
    with top[0]:
        st.metric("Route", explanation["route"])
    with top[1]:
        st.metric("Confidence", f"{float(row.get('decision_confidence', 0.0))*100:.1f}%")
    with top[2]:
        st.metric("Latency", f"{int(row.get('exec_ms', 0))} ms")
    with top[3]:
        st.metric("Score", f"{float(row.get('step_operational_score', 0.0)):.3f}")

    render_chip_row([
        (f"Confidence band · {explanation['confidence_band']}", "good" if explanation["confidence_band"] == "High" else "warn"),
        (f"Fallback · {explanation['fallback_triggered']}", "alert" if explanation["fallback_triggered"] else "good"),
        (f"Latency breach · {explanation['latency_breach']}", "alert" if explanation["latency_breach"] else "good"),
        (f"Backend · {explanation['backend_provider']}", "neutral"),
    ])

    cols = st.columns([1.15, 0.85])
    with cols[0]:
        render_summary_table([
            ("Scenario", row.get("scenario", "—")),
            ("Mode", row.get("mode", "—")),
            ("Active event", row.get("active_event", "none") or "none"),
            ("Primary hotspot", row.get("primary_hotspot_name", "—")),
            ("Route reason", explanation["route_reason"]),
        ], "Decision summary")
    with cols[1]:
        render_summary_table([
            ("Complexity score", row.get("complexity_score", "—")),
            ("Discrete ratio", row.get("discrete_ratio", "—")),
            ("Fallback reasons", ", ".join(explanation["fallback_reasons"]) if explanation["fallback_reasons"] else "—"),
            ("Backend id", explanation["backend_id"]),
            ("Queue ms", explanation["backend_queue_ms"] if explanation["backend_queue_ms"] is not None else "—"),
        ], "Execution context")

    st.markdown("### Dominant factors")
    if explanation["dominant_factors"]:
        render_chip_row([(f, "warn") for f in explanation["dominant_factors"]])
    else:
        st.caption("No dominant factors crossed the configured thresholds on this step.")

    breakdown_df = objective_breakdown_df(row)
    signal_df = trigger_signals_df(row)

    charts = st.columns(2)
    with charts[0]:
        if breakdown_df.empty:
            st.info("No objective breakdown available on this step.")
        else:
            fig = px.bar(
                breakdown_df,
                x="Weight",
                y="Objective term",
                orientation="h",
                template="plotly_dark",
                title="Objective breakdown",
            )
            fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=340, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, key=f"explainability_breakdown_{int(idx)}")
    with charts[1]:
        fig = px.bar(
            signal_df,
            x="Value",
            y="Signal",
            orientation="h",
            color="Exceeded",
            template="plotly_dark",
            title="Trigger signals vs thresholds",
            barmode="group",
        )
        fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=340)
        st.plotly_chart(fig, use_container_width=True, key=f"explainability_signals_{int(idx)}")

    with st.expander("Technical detail", expanded=False):
        tech = st.columns(3)
        with tech[0]:
            st.markdown("### Dispatch")
            st.json(safe_json_loads(row.get("dispatch_json")) or {})
        with tech[1]:
            st.markdown("### Quantum Request Envelope")
            st.json(explanation["qre"] or {"info": "No QRE generated on this step."})
        with tech[2]:
            st.markdown("### Quantum / backend result")
            st.json(explanation["result"] or {"info": "No backend result on this step."})

    st.markdown("### Signal table")
    st.dataframe(signal_df, use_container_width=True, hide_index=True, height=320)
