
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from mobility_os.io.run_store import RunStore


def list_replays(root: str | Path | None = None) -> List[Dict[str, Any]]:
    return RunStore(root).list_runs()


def load_replay_dataframe(run_id: str, root: str | Path | None = None) -> pd.DataFrame:
    return RunStore(root).read_records(run_id)


def load_replay_bundle(run_id: str, root: str | Path | None = None) -> Dict[str, Any]:
    return RunStore(root).load_run(run_id)


def build_replay_frame(df: pd.DataFrame, step_idx: int) -> Dict[str, Any]:
    if df.empty:
        return {"row": {}, "window_df": pd.DataFrame(), "step_idx": 0}
    idx = max(0, min(int(step_idx), len(df) - 1))
    row = df.iloc[idx].to_dict()
    window_df = df.iloc[max(0, idx - 8): min(len(df), idx + 9)].copy()
    return {"row": row, "window_df": window_df, "step_idx": idx}


def summarize_run(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        return {
            "steps": 0,
            "scenario": "—",
            "score_final": 0.0,
            "score_mean": 0.0,
            "fallback_rate": 0.0,
            "quantum_share": 0.0,
            "avg_latency_ms": 0.0,
            "max_risk": 0.0,
            "avg_confidence": 0.0,
        }
    return {
        "steps": int(len(df)),
        "scenario": str(df["scenario"].iloc[0]) if "scenario" in df.columns else "—",
        "score_final": float(df["step_operational_score"].iloc[-1]) if "step_operational_score" in df.columns else 0.0,
        "score_mean": float(df["step_operational_score"].mean()) if "step_operational_score" in df.columns else 0.0,
        "fallback_rate": float(df["fallback_triggered"].mean() * 100.0) if "fallback_triggered" in df.columns else 0.0,
        "quantum_share": float((df["decision_route"] == "QUANTUM").mean() * 100.0) if "decision_route" in df.columns else 0.0,
        "avg_latency_ms": float(df["exec_ms"].mean()) if "exec_ms" in df.columns else 0.0,
        "max_risk": float(df["risk_score"].max()) if "risk_score" in df.columns else 0.0,
        "avg_confidence": float(df["decision_confidence"].mean() * 100.0) if "decision_confidence" in df.columns else 0.0,
    }


def compare_runs(df_a: pd.DataFrame, df_b: pd.DataFrame, label_a: str = "Run A", label_b: str = "Run B") -> pd.DataFrame:
    a = summarize_run(df_a)
    b = summarize_run(df_b)
    metrics = [
        ("steps", "Steps"),
        ("score_final", "Final score"),
        ("score_mean", "Average score"),
        ("fallback_rate", "Fallback rate [%]"),
        ("quantum_share", "Quantum share [%]"),
        ("avg_latency_ms", "Average latency [ms]"),
        ("max_risk", "Max risk"),
        ("avg_confidence", "Average confidence [%]"),
    ]
    rows = []
    for key, name in metrics:
        av = a.get(key, 0.0)
        bv = b.get(key, 0.0)
        if isinstance(av, (int, float)) and isinstance(bv, (int, float)):
            delta = float(av) - float(bv)
        else:
            delta = 0.0
        rows.append({"Metric": name, label_a: av, label_b: bv, "Delta": delta})
    return pd.DataFrame(rows)
