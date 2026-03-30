from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable

from mobility_os.scenarios.loader import user_scenarios_path
from mobility_os.scenarios.presets import DEMO_PRESETS, DOMAIN_TEMPLATES, SHOCK_LIBRARY
from mobility_os.scenarios.schema import ScenarioSpec


ALLOWED_COMPLEXITIES = {"low", "medium", "high", "very_high", "extreme"}
ALLOWED_MODES = {"traffic", "safety", "logistics", "gateway", "event", "transit"}


def sanitize_scenario_id(value: str) -> str:
    value = value.strip().lower().replace(" ", "_")
    value = re.sub(r"[^a-z0-9_]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "custom_scenario"


def _merge_unique(seq_a: Iterable[str], seq_b: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen = set()
    for item in list(seq_a) + list(seq_b):
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


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


def apply_domain_template(payload: Dict[str, Any], template_id: str) -> Dict[str, Any]:
    template = DOMAIN_TEMPLATES.get(template_id, DOMAIN_TEMPLATES["none"])
    out = dict(payload)
    if template.get("mode"):
        out["mode"] = template["mode"]
    if template.get("complexity"):
        out["complexity"] = template["complexity"]
    out["trigger_events"] = _merge_unique(out.get("trigger_events", []), template.get("trigger_events", []))
    out["expected_subproblems"] = _merge_unique(out.get("expected_subproblems", []), template.get("expected_subproblems", []))
    out["recommended_interventions"] = _merge_unique(out.get("recommended_interventions", []), template.get("recommended_interventions", []))
    out["kpis"] = _merge_unique(out.get("kpis", []), template.get("kpis", []))
    out["disturbances"] = {**template.get("disturbances", {}), **out.get("disturbances", {})}
    return out


def apply_shocks(payload: Dict[str, Any], shock_ids: list[str]) -> Dict[str, Any]:
    out = dict(payload)
    note_parts = [str(out.get("note", "")).strip()] if str(out.get("note", "")).strip() else []
    for sid in shock_ids:
        shock = SHOCK_LIBRARY.get(sid)
        if not shock:
            continue
        out["trigger_events"] = _merge_unique(out.get("trigger_events", []), shock.get("events", []))
        out["disturbances"] = {**out.get("disturbances", {}), **shock.get("disturbances", {})}
        suffix = shock.get("note_suffix")
        if suffix:
            note_parts.append(str(suffix))
    out["note"] = " ".join(x for x in note_parts if x).strip()
    return out


def apply_demo_preset(payload: Dict[str, Any], preset_id: str) -> Dict[str, Any]:
    preset = DEMO_PRESETS.get(preset_id, DEMO_PRESETS["none"])
    out = apply_domain_template(payload, preset.get("template", "none"))
    out = apply_shocks(out, list(preset.get("shocks", [])))
    return out


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


def save_custom_scenario(payload: Dict[str, Any]):
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
