
from __future__ import annotations

import io

import pandas as pd
import plotly.express as px
import streamlit as st

from mobility_os.runtime.benchmark import aggregate_benchmark, benchmark_runs, best_seed_per_scenario
from mobility_os.ui.components import chart_key, render_kpi_row, render_summary_table


def _parse_seeds(text: str) -> list[int]:
    seeds: list[int] = []
    for token in (text or "").split(","):
        token = token.strip()
        if not token:
            continue
        try:
            seeds.append(int(token))
        except Exception:
            continue
    return seeds or [42]


def render_benchmark_tab(scenarios: dict) -> None:
    st.markdown("## Benchmark Batch")
    ss = st.session_state
    ss.setdefault("benchmark_df", pd.DataFrame())

    left, right = st.columns([1.0, 1.0])
    with left:
        selected = st.multiselect(
            "Scenarios",
            options=list(scenarios.keys()),
            default=list(scenarios.keys())[: min(3, len(scenarios))],
            format_func=lambda x: scenarios[x].title,
            key="benchmark_scenarios",
        )
        steps = st.slider("Benchmark steps", 8, 96, 24, step=4, key="benchmark_steps")
    with right:
        seeds_text = st.text_input("Seeds (comma separated)", value="11,22,33", key="benchmark_seeds")
        run_clicked = st.button("Run benchmark batch", use_container_width=True)

    if run_clicked:
        seeds = _parse_seeds(seeds_text)
        with st.spinner("Running benchmark batch..."):
            ss["benchmark_df"] = benchmark_runs(selected, seeds, int(steps))

    df = ss.get("benchmark_df", pd.DataFrame())
    if df.empty:
        st.info("Run a benchmark batch to compare scenarios and seeds.")
        return

    summary_df = aggregate_benchmark(df)
    best_df = best_seed_per_scenario(df)

    render_kpi_row([
        ("Runs", len(df)),
        ("Scenarios", df["scenario"].nunique()),
        ("Seeds", df["seed"].nunique()),
        ("Best avg score", f'{float(df["avg_operational_score"].max()):.3f}'),
        ("Avg quantum share", f'{float(df["quantum_share"].mean()) * 100:.1f}%'),
        ("Avg fallback share", f'{float(df["fallback_share"].mean()) * 100:.1f}%'),
    ])

    downloads = st.columns([0.7, 1.3])
    with downloads[0]:
        st.download_button(
            "Download benchmark CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="benchmark_runs.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with downloads[1]:
        render_summary_table([
            ("Top scenario", summary_df.iloc[0]["scenario"] if not summary_df.empty else "—"),
            ("Top scenario score", round(float(summary_df.iloc[0]["avg_operational_score"]), 4) if not summary_df.empty else "—"),
            ("Best seed run", f'{best_df.iloc[0]["scenario"]} / {int(best_df.iloc[0]["seed"])}' if not best_df.empty else "—"),
        ], "Benchmark highlights")

    charts = st.columns(2)
    with charts[0]:
        fig = px.bar(
            summary_df,
            x="scenario",
            y="avg_operational_score",
            template="plotly_dark",
            title="Average operational score by scenario",
        )
        fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=340)
        st.plotly_chart(fig, use_container_width=True, key=chart_key("benchmark", "score_by_scenario"))
    with charts[1]:
        fig = px.bar(
            summary_df,
            x="scenario",
            y="avg_exec_ms",
            template="plotly_dark",
            title="Average latency by scenario",
        )
        fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=340)
        st.plotly_chart(fig, use_container_width=True, key=chart_key("benchmark", "latency_by_scenario"))

    charts2 = st.columns(2)
    with charts2[0]:
        fig = px.scatter(
            df,
            x="avg_risk",
            y="avg_operational_score",
            color="scenario",
            symbol="seed",
            template="plotly_dark",
            title="Risk vs operational score",
        )
        fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=360)
        st.plotly_chart(fig, use_container_width=True, key=chart_key("benchmark", "risk_vs_score"))
    with charts2[1]:
        fig = px.scatter(
            df,
            x="quantum_share",
            y="fallback_share",
            color="scenario",
            symbol="seed",
            template="plotly_dark",
            title="Quantum share vs fallback share",
        )
        fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=360)
        st.plotly_chart(fig, use_container_width=True, key=chart_key("benchmark", "quantum_vs_fallback"))

    st.markdown("### Aggregated scenario summary")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    st.markdown("### Best seed per scenario")
    st.dataframe(best_df, use_container_width=True, hide_index=True)

    st.markdown("### Raw benchmark runs")
    st.dataframe(df, use_container_width=True, hide_index=True)
