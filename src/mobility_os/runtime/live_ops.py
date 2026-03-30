from __future__ import annotations

from typing import Any


def step_many(runtime, steps: int) -> None:
    for _ in range(max(0, int(steps))):
        runtime.step()


def should_auto_pause(latest: dict[str, Any]) -> tuple[bool, str]:
    if not latest:
        return False, ""
    risk = float(latest.get("risk_score", 0.0) or 0.0)
    gateway = float(latest.get("gateway_delay_index", 0.0) or 0.0)
    bunching = float(latest.get("bus_bunching_index", 0.0) or 0.0)
    event = str(latest.get("active_event", "none") or "none")
    if risk >= 0.82:
        return True, "Auto-paused: critical safety risk threshold reached."
    if gateway >= 0.88:
        return True, "Auto-paused: gateway delay is in critical range."
    if bunching >= 0.86 and event in {"event_release", "incident", "gateway_surge"}:
        return True, "Auto-paused: severe service instability under disruptive event."
    return False, ""


def live_status_payload(df, latest: dict[str, Any], running: bool) -> dict[str, Any]:
    rows = len(df) if hasattr(df, "__len__") else 0
    return {
        "running": running,
        "steps": int(rows),
        "event": latest.get("active_event", "none") if latest else "none",
        "route": latest.get("decision_route", "—") if latest else "—",
        "hotspot": latest.get("primary_hotspot_name", "—") if latest else "—",
    }
