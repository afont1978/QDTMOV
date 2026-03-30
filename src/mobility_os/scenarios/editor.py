from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict

from mobility_os.scenarios.loader import load_scenarios, user_scenarios_path
from mobility_os.scenarios.schema import EventScheduleEntry, ScenarioSpec


ALLOWED_COMPLEXITIES = {"low", "medium", "high", "very_high", "extreme"}
ALLOWED_MODES = {"traffic", "safety", "logistics", "gateway", "event", "transit"}


def sanitize_scenario_id(value: str) -> str:
    value = value.strip().lower().replace(" ", "_")
    value = re.sub(r"[^a-z0-9_]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "custom_scenario"


def scenario_to_editor_dict(spec: ScenarioSpec) -> Dict[str, Any]:
    return {
        "id": spec.id,
        "title": spec.title,
        "mode": spec.mode,
        "complexity": spec.complexity,
        "primary_hotspots": list(spec.primary_hotspots),
        "trigger_events": list(spec.trigger_events),
        "disturbances": dict(spec.disturbances),
        "expected_subproblems": list(spec.expected_subproblems),
        "recommended_interventions": list(spec.recommended_interventions),
        "kpis": list(spec.kpis),
        "note": spec.note,
        "twin_hotspots": dict(spec.twin_hotspots),
    }


def validate_editor_payload(payload: Dict[str, Any]) -> list[str]:
    errors: list[str] = []
    sid = sanitize_scenario_id(str(payload.get("id", "")))
    if not sid:
        errors.append("Scenario id is required.")
    if not str(payload.get("title", "")).strip():
        errors.append("Title is required.")
    if str(payload.get("complexity", "medium")).strip() not in ALLOWED_COMPLEXITIES:
        errors.append("Complexity must be one of: low, medium, high, very_high, extreme.")
    mode = str(payload.get("mode", "traffic")).strip()
    if mode not in ALLOWED_MODES:
        errors.append("Mode must be one of: traffic, safety, logistics, gateway, event, transit.")
    if not payload.get("primary_hotspots"):
        errors.append("At least one primary hotspot is required.")
    return errors


def build_custom_spec(payload: Dict[str, Any]) -> ScenarioSpec:
    sid = sanitize_scenario_id(str(payload.get("id", "")))
    return ScenarioSpec(
        id=sid,
        title=str(payload.get("title", sid.replace("_", " ").title())).strip(),
        mode=str(payload.get("mode", "traffic")).strip(),
        complexity=str(payload.get("complexity", "medium")).strip(),
        primary_hotspots=list(payload.get("primary_hotspots", [])),
        trigger_events=list(payload.get("trigger_events", [])),
        disturbances=dict(payload.get("disturbances", {})),
        expected_subproblems=list(payload.get("expected_subproblems", [])),
        recommended_interventions=list(payload.get("recommended_interventions", [])),
        kpis=list(payload.get("kpis", [])),
        note=str(payload.get("note", "")).strip(),
        twin_hotspots=dict(payload.get("twin_hotspots", {})),
    )


def save_custom_scenario(payload: Dict[str, Any]) -> Path:
    errors = validate_editor_payload(payload)
    if errors:
        raise ValueError("\n".join(errors))

    spec = build_custom_spec(payload)
    path = user_scenarios_path()
    current = {}
    if path.exists():
        current = json.loads(path.read_text(encoding="utf-8"))
    current[spec.id] = spec.model_dump()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def custom_scenarios_exist() -> bool:
    return user_scenarios_path().exists()
