from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from mobility_os.runtime.explainability import (
    active_hotspots_df,
    explain_route_decision,
    impact_chain_df,
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
        (f"Cascade score · {explanation['network_cascade_score']:.2f}", "warn" if explanation["network_cascade_score"] >= 0.45 else "neutral"),
        (f"Hotspots · {explanation['hotspot_count']}", "warn" if explanation["hotspot_count"] >= 3 else "neutral"),
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
            ("Exec ms", explanation["backend_exec_ms"] if explanation["backend_exec_ms"] is not None else "—"),
            ("Impact chain links", explanation["impact_chain_links"]),
        ], "Decision envelope")

    st.subheader("Dominant decision factors")
    if explanation["dominant_factors"]:
        for factor in explanation["dominant_factors"]:
            st.caption(f"• {factor}")
    else:
        st.caption("No dominant threshold-crossing factors identified.")

    active_df = active_hotspots_df(row)
    chain_df = impact_chain_df(row)

    mid = st.columns(2)
    with mid[0]:
        signals = trigger_signals_df(row)
        if not signals.empty:
            st.dataframe(signals, use_container_width=True, hide_index=True, height=330)
    with mid[1]:
        breakdown = objective_breakdown_df(row)
        if not breakdown.empty:
            fig = px.bar(breakdown, x="Weight", y="Objective term", orientation="h", template="plotly_dark", title="Objective breakdown")
            fig.update_layout(height=330, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, use_container_width=True, key=f"explainability_objective_{row.get('step_id',0)}")

    lower = st.columns(2)
    with lower[0]:
        st.subheader("Active hotspots cluster")
        if active_df.empty:
            st.caption("No propagated hotspot cluster available.")
        else:
            st.dataframe(active_df, use_container_width=True, hide_index=True, height=260)
    with lower[1]:
        st.subheader("Impact chain")
        if chain_df.empty:
            st.caption("No impact chain available.")
        else:
            st.dataframe(chain_df, use_container_width=True, hide_index=True, height=260)

    with st.expander("Technical detail", expanded=False):
        tech_cols = st.columns(3)
        with tech_cols[0]:
            st.markdown("### Dispatch")
            st.json(safe_json_loads(row.get("dispatch_json")) or {})
        with tech_cols[1]:
            st.markdown("### Quantum Request Envelope")
            st.json(safe_json_loads(row.get("qre_json")) or {"info": "No QRE generated on this step."})
        with tech_cols[2]:
            st.markdown("### Quantum Result")
            st.json(safe_json_loads(row.get("result_json")) or {"info": "No quantum result on this step."})
