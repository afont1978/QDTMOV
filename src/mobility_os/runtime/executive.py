from __future__ import annotations

from typing import Any

import pandas as pd


SUBSYSTEM_ORDER = ["Traffic", "Transit", "Risk", "Logistics", "Gateway"]


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _latest(df: pd.DataFrame) -> dict[str, Any]:
    return {} if df.empty else df.iloc[-1].to_dict()


def subsystem_scores(latest: dict[str, Any]) -> dict[str, float]:
    if not latest:
        return {k: 0.0 for k in SUBSYSTEM_ORDER}
    traffic = _clip01(latest.get("network_speed_index", 0.0))
    transit = _clip01(0.65 * (1.0 - float(latest.get("bus_bunching_index", 0.0) or 0.0)) + 0.35 * min(float(latest.get("bus_commercial_speed_kmh", 0.0) or 0.0) / 18.0, 1.0))
    risk = _clip01(1.0 - float(latest.get("risk_score", 0.0) or 0.0))
    curb_pressure = 0.55 * float(latest.get("curb_occupancy_rate", 0.0) or 0.0) + 0.45 * float(latest.get("illegal_curb_occupancy_rate", 0.0) or 0.0)
    logistics = _clip01(1.0 - curb_pressure)
    gateway = _clip01(1.0 - float(latest.get("gateway_delay_index", 0.0) or 0.0))
    return {
        "Traffic": traffic,
        "Transit": transit,
        "Risk": risk,
        "Logistics": logistics,
        "Gateway": gateway,
    }


def subsystem_scores_df(latest: dict[str, Any]) -> pd.DataFrame:
    scores = subsystem_scores(latest)
    return pd.DataFrame({"Subsystem": list(scores.keys()), "Score": list(scores.values())})


def executive_status(score: float) -> str:
    score = float(score)
    if score >= 0.75:
        return "Green"
    if score >= 0.50:
        return "Amber"
    return "Red"


def executive_snapshot(df: pd.DataFrame) -> dict[str, Any]:
    latest = _latest(df)
    subsystems = subsystem_scores(latest)
    city_score = _clip01(latest.get("step_operational_score", 0.0))
    return {
        "city_score": city_score,
        "city_status": executive_status(city_score),
        "subsystems": subsystems,
        "route": latest.get("decision_route", "—"),
        "hotspot": latest.get("primary_hotspot_name", "—"),
        "active_event": latest.get("active_event", "none") or "none",
        "latency_ms": int(latest.get("exec_ms", 0) or 0),
        "confidence": float(latest.get("decision_confidence", 0.0) or 0.0),
        "fallback_triggered": bool(latest.get("fallback_triggered", False)),
    }


def trend_delta(df: pd.DataFrame, col: str, window: int = 15) -> float:
    if df.empty or col not in df.columns or len(df) < 2:
        return 0.0
    work = df.tail(max(window, 2))
    first = float(work.iloc[0][col])
    last = float(work.iloc[-1][col])
    return last - first


def trend_table(df: pd.DataFrame, windows: tuple[int, ...] = (15, 30, 60)) -> pd.DataFrame:
    latest = _latest(df)
    rows = []
    metrics = {
        "City score": "step_operational_score",
        "Network speed": "network_speed_index",
        "Risk": "risk_score",
        "Gateway delay": "gateway_delay_index",
    }
    for label, col in metrics.items():
        row = {"Metric": label, "Current": round(float(latest.get(col, 0.0) or 0.0), 4)}
        for w in windows:
            row[f"Δ{w}"] = round(trend_delta(df, col, w), 4)
        rows.append(row)
    return pd.DataFrame(rows)


def pressure_ranking_df(latest: dict[str, Any]) -> pd.DataFrame:
    if not latest:
        return pd.DataFrame(columns=["Pressure", "Value"])
    pressures = {
        "Risk score": float(latest.get("risk_score", 0.0) or 0.0),
        "Gateway delay": float(latest.get("gateway_delay_index", 0.0) or 0.0),
        "Bus bunching": float(latest.get("bus_bunching_index", 0.0) or 0.0),
        "Curb occupancy": float(latest.get("curb_occupancy_rate", 0.0) or 0.0),
        "Illegal curb occupancy": float(latest.get("illegal_curb_occupancy_rate", 0.0) or 0.0),
        "Pedestrian exposure": float(latest.get("pedestrian_exposure", 0.0) or 0.0),
    }
    return pd.DataFrame({"Pressure": list(pressures.keys()), "Value": list(pressures.values())}).sort_values("Value", ascending=False).reset_index(drop=True)


def route_mix_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "decision_route" not in df.columns:
        return pd.DataFrame(columns=["Route", "Count"])
    vc = df["decision_route"].value_counts().reset_index()
    vc.columns = ["Route", "Count"]
    return vc


def subsystem_status_rows(latest: dict[str, Any]) -> list[tuple[str, str, float]]:
    rows = []
    for name, score in subsystem_scores(latest).items():
        rows.append((name, executive_status(score), round(score, 3)))
    return rows
