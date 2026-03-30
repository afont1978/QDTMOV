from __future__ import annotations

import json
from typing import Any, Dict

import pandas as pd


def safe_json_loads(value: Any) -> Any:
    if value in (None, "", {}):
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return None


def objective_breakdown_df(row: Dict[str, Any]) -> pd.DataFrame:
    payload = safe_json_loads(row.get("objective_breakdown_json")) or {}
    if not isinstance(payload, dict) or not payload:
        return pd.DataFrame(columns=["Objective term", "Weight"])
    df = pd.DataFrame(
        [{"Objective term": str(k).replace("_", " ").title(), "Weight": float(v)} for k, v in payload.items()]
    )
    return df.sort_values("Weight", ascending=False).reset_index(drop=True)


def trigger_signals_df(row: Dict[str, Any]) -> pd.DataFrame:
    signals = [
        ("Risk score", float(row.get("risk_score", 0.0) or 0.0), 0.58),
        ("Bus bunching", float(row.get("bus_bunching_index", 0.0) or 0.0), 0.30),
        ("Gateway delay", float(row.get("gateway_delay_index", 0.0) or 0.0), 0.52),
        ("Curb occupancy", float(row.get("curb_occupancy_rate", 0.0) or 0.0), 0.72),
        ("Illegal curb occupancy", float(row.get("illegal_curb_occupancy_rate", 0.0) or 0.0), 0.22),
        ("Complexity score", float(row.get("complexity_score", 0.0) or 0.0), 4.70),
        ("Discrete ratio", float(row.get("discrete_ratio", 0.0) or 0.0), 0.40),
        ("Cascade score", float(row.get("network_cascade_score", 0.0) or 0.0), 0.42),
        ("Hotspot count", float(row.get("hotspot_count", 1) or 1), 2.00),
    ]
    rows = []
    for label, value, threshold in signals:
        rows.append(
            {
                "Signal": label,
                "Value": round(value, 4),
                "Threshold": threshold,
                "Exceeded": bool(value >= threshold),
                "Gap": round(value - threshold, 4),
            }
        )
    return pd.DataFrame(rows)


def active_hotspots_df(row: Dict[str, Any]) -> pd.DataFrame:
    payload = safe_json_loads(row.get("active_hotspots_json")) or []
    if not isinstance(payload, list) or not payload:
        return pd.DataFrame(columns=["name", "severity", "depth", "event_type", "impacted_subsystems"])
    df = pd.DataFrame(payload)
    if "impacted_subsystems" in df.columns:
        df["impacted_subsystems"] = df["impacted_subsystems"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
    return df.sort_values(["severity", "depth"], ascending=[False, True]).reset_index(drop=True)


def impact_chain_df(row: Dict[str, Any]) -> pd.DataFrame:
    payload = safe_json_loads(row.get("impact_chain_json")) or []
    if not isinstance(payload, list) or not payload:
        return pd.DataFrame(columns=["from_hotspot", "to_hotspot", "transferred_severity", "depth", "rationale"])
    df = pd.DataFrame(payload)
    return df.sort_values(["transferred_severity", "depth"], ascending=[False, True]).reset_index(drop=True)


def explain_route_decision(row: Dict[str, Any]) -> Dict[str, Any]:
    qre = safe_json_loads(row.get("qre_json")) or {}
    result = safe_json_loads(row.get("result_json")) or {}
    fallback_reasons = row.get("fallback_reasons") or []
    confidence = float(row.get("decision_confidence", 0.0) or 0.0)

    dominant_factors = []
    signals_df = trigger_signals_df(row)
    exceeded = signals_df[signals_df["Exceeded"]]
    if not exceeded.empty:
        dominant_factors = exceeded.sort_values("Gap", ascending=False)["Signal"].head(4).tolist()

    backend = {}
    if isinstance(result, dict):
        backend = result.get("backend", {}) or {}

    active_df = active_hotspots_df(row)
    chain_df = impact_chain_df(row)

    return {
        "route": row.get("decision_route", "—"),
        "route_reason": row.get("route_reason", "No route explanation available."),
        "confidence_band": (
            "High" if confidence >= 0.85 else "Medium" if confidence >= 0.72 else "Low"
        ),
        "fallback_triggered": bool(row.get("fallback_triggered", False)),
        "fallback_reasons": fallback_reasons,
        "latency_breach": bool(row.get("latency_breach", False)),
        "dominant_factors": dominant_factors,
        "backend_provider": backend.get("provider", "CLASSICAL"),
        "backend_id": backend.get("backend_id", "deterministic"),
        "backend_queue_ms": backend.get("queue_ms"),
        "backend_exec_ms": backend.get("exec_ms"),
        "hotspot_count": int(row.get("hotspot_count", 1) or 1),
        "network_cascade_score": float(row.get("network_cascade_score", 0.0) or 0.0),
        "top_propagated_hotspots": active_df["name"].head(3).tolist() if not active_df.empty else [],
        "impact_chain_links": len(chain_df),
        "qre": qre,
        "result": result,
    }
