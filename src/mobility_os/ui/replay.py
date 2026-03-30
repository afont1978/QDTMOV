
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from mobility_os.io.run_store import RunStore
from mobility_os.runtime.replay import build_replay_frame, compare_runs, list_replays, load_replay_bundle, summarize_run
from mobility_os.ui.charts import make_line, make_route_mix_chart, make_subsystem_score_chart
from mobility_os.ui.components import chart_key, render_kpi_row, render_summary_table


def _run_label(manifest: dict) -> str:
    title = manifest.get("title") or manifest.get("scenario") or "Run"
    scenario = manifest.get("scenario", "—")
    run_id = manifest.get("run_id", "—")
    updated = manifest.get("updated_at") or manifest.get("created_at") or "—"
    records = manifest.get("records", 0)
    return f"{title} · {scenario} · {records} records · {run_id} · {updated}"


def _comparison_line(df_a: pd.DataFrame, df_b: pd.DataFrame, label_a: str, label_b: str, metric: str):
    rows = []
    if metric in df_a.columns:
        for _, row in df_a[["step_id", metric]].dropna().iterrows():
            rows.append({"Step": int(row["step_id"]), "Value": float(row[metric]), "Run": label_a})
    if metric in df_b.columns:
        for _, row in df_b[["step_id", metric]].dropna().iterrows():
            rows.append({"Step": int(row["step_id"]), "Value": float(row[metric]), "Run": label_b})
    if not rows:
        return px.line(title=f"{metric} comparison")
    plot_df = pd.DataFrame(rows)
    fig = px.line(plot_df, x="Step", y="Value", color="Run", template="plotly_dark", title=f"{metric.replace('_', ' ').title()} comparison")
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=320)
    return fig


def render_replay_tab() -> None:
    st.markdown("## Replay & Run Comparison")
    manifests = list_replays()
    if not manifests:
        st.info("No saved runs available yet. Execute some steps first and return to this tab.")
        return

    manifest_map = {m["run_id"]: m for m in manifests if "run_id" in m}
    run_ids = list(manifest_map.keys())

    selectors = st.columns([1.2, 1.2, 0.8])
    with selectors[0]:
        primary_run_id = st.selectbox("Primary run", run_ids, format_func=lambda rid: _run_label(manifest_map[rid]))
    with selectors[1]:
        compare_options = ["—"] + run_ids
        secondary_run_id = st.selectbox("Comparison run", compare_options, index=0, format_func=lambda rid: "—" if rid == "—" else _run_label(manifest_map[rid]))
    with selectors[2]:
        st.caption("Use the same run twice only if you want to inspect a single replay without comparison.")

    primary_bundle = load_replay_bundle(primary_run_id)
    primary_manifest = primary_bundle["manifest"]
    primary_df = primary_bundle["records"]

    if primary_df.empty:
        st.warning("The selected run has no records yet.")
        return

    summary = summarize_run(primary_df)
    render_kpi_row([
        ("Run", primary_manifest.get("run_id", "—")),
        ("Scenario", summary["scenario"]),
        ("Steps", summary["steps"]),
        ("Avg score", f'{summary["score_mean"]:.3f}'),
        ("Fallback rate", f'{summary["fallback_rate"]:.1f}%'),
        ("Quantum share", f'{summary["quantum_share"]:.1f}%'),
    ])

    top = st.columns([1.1, 0.9])
    with top[0]:
        step_idx = st.slider("Replay step", 0, max(0, len(primary_df) - 1), max(0, len(primary_df) - 1), key=f"replay_step_{primary_run_id}")
    with top[1]:
        store = RunStore()
        st.download_button(
            "Download run CSV",
            data=store.export_run_csv_bytes(primary_run_id),
            file_name=f"{primary_run_id}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    frame = build_replay_frame(primary_df, step_idx)
    row = frame["row"]
    window_df = frame["window_df"]

    details = st.columns([1.05, 1.05, 0.9])
    with details[0]:
        render_summary_table([
            ("Run ID", primary_manifest.get("run_id", "—")),
            ("Scenario", row.get("scenario", "—")),
            ("Step", row.get("step_id", "—")),
            ("Timestamp", row.get("ts", "—")),
            ("Hotspot", row.get("primary_hotspot_name", "—")),
        ], "Replay frame")
    with details[1]:
        render_summary_table([
            ("Decision route", row.get("decision_route", "—")),
            ("Route reason", row.get("route_reason", "—")),
            ("Fallback", row.get("fallback_triggered", "—")),
            ("Latency [ms]", row.get("exec_ms", "—")),
            ("Confidence", round(float(row.get("decision_confidence", 0.0)) * 100.0, 2)),
        ], "Decision state")
    with details[2]:
        st.plotly_chart(
            make_subsystem_score_chart(row),
            use_container_width=True,
            key=chart_key("replay", "subsystem_score", row, primary_run_id),
        )

    charts = st.columns(2)
    with charts[0]:
        st.plotly_chart(
            make_line(primary_df, ["network_speed_index", "corridor_reliability_index", "step_operational_score"], "Replay evolution"),
            use_container_width=True,
            key=chart_key("replay", "evolution", row, primary_run_id),
        )
    with charts[1]:
        st.plotly_chart(
            make_route_mix_chart(primary_df),
            use_container_width=True,
            key=chart_key("replay", "route_mix", row, primary_run_id),
        )

    charts2 = st.columns(2)
    with charts2[0]:
        st.plotly_chart(
            make_line(window_df, ["risk_score", "near_miss_index", "pedestrian_exposure"], "Local replay risk window"),
            use_container_width=True,
            key=chart_key("replay", "risk_window", row, primary_run_id),
        )
    with charts2[1]:
        st.plotly_chart(
            make_line(window_df, ["bus_bunching_index", "curb_occupancy_rate", "gateway_delay_index"], "Local replay pressure window"),
            use_container_width=True,
            key=chart_key("replay", "pressure_window", row, primary_run_id),
        )

    st.dataframe(primary_df.tail(min(60, len(primary_df))), use_container_width=True, height=260, hide_index=True)

    if secondary_run_id != "—":
        secondary_bundle = load_replay_bundle(secondary_run_id)
        secondary_df = secondary_bundle["records"]
        if not secondary_df.empty:
            st.markdown("### Run comparison")
            compare_df = compare_runs(primary_df, secondary_df, primary_run_id, secondary_run_id)
            st.dataframe(compare_df, use_container_width=True, hide_index=True)
            compare_cols = st.columns(2)
            with compare_cols[0]:
                st.plotly_chart(
                    _comparison_line(primary_df, secondary_df, primary_run_id, secondary_run_id, "step_operational_score"),
                    use_container_width=True,
                    key=chart_key("replay", "comparison_score", row, f"{primary_run_id}_{secondary_run_id}"),
                )
            with compare_cols[1]:
                st.plotly_chart(
                    _comparison_line(primary_df, secondary_df, primary_run_id, secondary_run_id, "risk_score"),
                    use_container_width=True,
                    key=chart_key("replay", "comparison_risk", row, f"{primary_run_id}_{secondary_run_id}"),
                )
