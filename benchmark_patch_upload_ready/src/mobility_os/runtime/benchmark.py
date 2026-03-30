
from __future__ import annotations

from typing import Iterable, List
import pandas as pd

from mobility_os.runtime.runtime import MobilityRuntime


def benchmark_runs(scenarios: Iterable[str], seeds: Iterable[int], steps: int = 48) -> pd.DataFrame:
    rows: List[dict] = []
    for scenario in scenarios:
        for seed in seeds:
            rt = MobilityRuntime(scenario=scenario, seed=seed)
            for _ in range(steps):
                rt.step()
            df = rt.dataframe()
            rows.append({
                "scenario": scenario,
                "seed": seed,
                "steps": steps,
                "avg_operational_score": float(df["step_operational_score"].mean()),
                "final_operational_score": float(df["step_operational_score"].iloc[-1]),
                "avg_exec_ms": float(df["exec_ms"].mean()),
                "quantum_share": float((df["decision_route"] == "QUANTUM").mean()),
                "fallback_share": float(df["fallback_triggered"].mean()),
                "avg_risk": float(df["risk_score"].mean()),
                "avg_network_speed": float(df["network_speed_index"].mean()),
                "avg_gateway_delay": float(df["gateway_delay_index"].mean()),
            })
    return pd.DataFrame(rows)


def aggregate_benchmark(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[
            "scenario", "runs", "steps", "avg_operational_score", "final_operational_score",
            "avg_exec_ms", "quantum_share", "fallback_share", "avg_risk",
            "avg_network_speed", "avg_gateway_delay"
        ])
    grouped = (
        df.groupby("scenario", as_index=False)
        .agg(
            runs=("seed", "count"),
            steps=("steps", "max"),
            avg_operational_score=("avg_operational_score", "mean"),
            final_operational_score=("final_operational_score", "mean"),
            avg_exec_ms=("avg_exec_ms", "mean"),
            quantum_share=("quantum_share", "mean"),
            fallback_share=("fallback_share", "mean"),
            avg_risk=("avg_risk", "mean"),
            avg_network_speed=("avg_network_speed", "mean"),
            avg_gateway_delay=("avg_gateway_delay", "mean"),
        )
        .sort_values("avg_operational_score", ascending=False)
        .reset_index(drop=True)
    )
    return grouped


def best_seed_per_scenario(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=df.columns)
    idx = df.groupby("scenario")["avg_operational_score"].idxmax()
    return df.loc[idx].sort_values("avg_operational_score", ascending=False).reset_index(drop=True)
