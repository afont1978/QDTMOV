from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Dict, List, Tuple


EVENT_BASE = {
    "incident": 0.95,
    "rain_event": 0.70,
    "school_peak": 0.76,
    "bus_bunching": 0.72,
    "delivery_wave": 0.78,
    "illegal_curb_occupation": 0.74,
    "gateway_surge": 0.84,
    "event_release": 0.86,
    "demand_spike": 0.68,
    None: 0.45,
}

EVENT_SUBSYSTEM_PUSH = {
    "incident": ["traffic", "gateway", "risk"],
    "rain_event": ["risk", "traffic"],
    "school_peak": ["risk", "transit"],
    "bus_bunching": ["transit", "traffic"],
    "delivery_wave": ["logistics", "risk"],
    "illegal_curb_occupation": ["logistics", "risk"],
    "gateway_surge": ["gateway", "traffic", "logistics"],
    "event_release": ["transit", "traffic", "risk"],
    "demand_spike": ["traffic", "transit"],
    None: ["traffic"],
}


def _default_dependencies(primary_hotspots: List[str]) -> Dict[str, List[str]]:
    deps: Dict[str, List[str]] = defaultdict(list)
    for idx, name in enumerate(primary_hotspots):
        if idx > 0:
            deps[name].append(primary_hotspots[idx - 1])
        if idx < len(primary_hotspots) - 1:
            deps[name].append(primary_hotspots[idx + 1])
    return dict(deps)


def _subsystems_from_category(category: str, event_type: str | None) -> List[str]:
    cat = str(category).lower()
    subs = set(EVENT_SUBSYSTEM_PUSH.get(event_type, EVENT_SUBSYSTEM_PUSH[None]))
    if "aeroport" in cat or "gateway" in cat:
        subs.add("gateway")
        subs.add("traffic")
    if "logístic" in cat or "logistic" in cat or "port" in cat or "curb" in cat or "cruceros" in cat:
        subs.add("logistics")
    if "intermodal" in cat or "bus" in cat or "metro" in cat or "tranv" in cat:
        subs.add("transit")
    if "turismo" in cat or "urbano" in cat or "peat" in cat:
        subs.add("risk")
    return sorted(subs)


def _event_base_severity(active_event: str | None, metrics: Dict[str, float]) -> float:
    base = EVENT_BASE.get(active_event, 0.60)
    metric_push = max(
        float(metrics.get("risk_score", 0.0) or 0.0),
        float(metrics.get("gateway_delay_index", 0.0) or 0.0),
        float(metrics.get("bus_bunching_index", 0.0) or 0.0),
        float(metrics.get("curb_pressure_index", 0.0) or 0.0),
        1.0 - min(float(metrics.get("network_speed_index", 0.0) or 0.0), 1.0),
    )
    return min(1.0, 0.55 * base + 0.45 * metric_push)


def build_propagation_view(spec, hotspots: Dict[str, Any], primary_name: str, active_event: str | None, metrics: Dict[str, float]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], float]:
    dependencies = spec.hotspot_dependencies or _default_dependencies(list(spec.primary_hotspots))
    if not dependencies and primary_name:
        dependencies = {primary_name: []}

    root_severity = _event_base_severity(active_event, metrics)
    seen: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []

    queue = deque()
    queue.append((primary_name, root_severity, 0, "origin"))
    visited_best: Dict[str, float] = {}

    while queue:
        name, severity, depth, source = queue.popleft()
        if not name or name not in hotspots:
            continue
        if severity < 0.18:
            continue
        if visited_best.get(name, -1) >= severity:
            continue
        visited_best[name] = severity

        hotspot = hotspots[name]
        seen[name] = {
            "name": name,
            "lat": hotspot.lat,
            "lon": hotspot.lon,
            "category": hotspot.category,
            "streets": hotspot.streets,
            "severity": round(float(severity), 4),
            "depth": depth,
            "source": source,
            "event_type": active_event or "none",
            "impacted_subsystems": _subsystems_from_category(hotspot.category, active_event),
        }

        for neighbor in dependencies.get(name, []):
            next_severity = round(float(severity * (0.74 if depth == 0 else 0.82)), 4)
            edges.append({
                "from_hotspot": name,
                "to_hotspot": neighbor,
                "transferred_severity": next_severity,
                "depth": depth + 1,
                "event_type": active_event or "none",
                "rationale": f"{active_event or 'network pressure'} propagated from {name} to {neighbor}",
            })
            if depth < 2:
                queue.append((neighbor, next_severity, depth + 1, name))

    active_hotspots = sorted(seen.values(), key=lambda x: (-x["severity"], x["depth"], x["name"]))
    impact_chain = sorted(edges, key=lambda x: (-x["transferred_severity"], x["depth"], x["from_hotspot"], x["to_hotspot"]))
    cascade_score = round(sum(item["severity"] for item in active_hotspots) / max(len(active_hotspots), 1), 4)
    return active_hotspots, impact_chain, cascade_score
