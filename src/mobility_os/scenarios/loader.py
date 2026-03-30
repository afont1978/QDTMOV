from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Dict

from mobility_os.scenarios.schema import ScenarioSpec


def _root() -> Path:
    return Path(__file__).resolve().parents[3]


def _scenario_paths() -> tuple[Path, Path, Path]:
    root = _root()
    return (
        root / "data" / "scenarios" / "scenario_library.json",
        root / "data" / "scenarios" / "scenario_library_high_complexity_v2.json",
        root / "data" / "scenarios" / "scenario_meta.json",
    )


def user_scenarios_path() -> Path:
    env_path = os.getenv("QDTMOV_USER_SCENARIOS_PATH")
    if env_path:
        return Path(env_path)
    tmpdir = Path(tempfile.gettempdir()) / "qdtmov"
    tmpdir.mkdir(parents=True, exist_ok=True)
    return tmpdir / "user_scenarios.json"


def _load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _spec_from_base(sid: str, payload: dict, meta: dict) -> ScenarioSpec:
    return ScenarioSpec(
        id=sid,
        title=meta.get("title", sid.replace("_", " ").title()),
        mode=payload.get("mode", "traffic"),
        complexity=meta.get("complexity", "medium"),
        primary_hotspots=meta.get("primary_hotspots", []),
        trigger_events=list(payload.get("event_schedule", {}).keys()),
        event_schedule=payload.get("event_schedule", {}),
        shocks=payload.get("shocks", {}),
        note=meta.get("note", ""),
        twin_hotspots=meta.get("twin_hotspots", {}),
        hotspot_dependencies=meta.get("hotspot_dependencies", {}),
        compound_events=meta.get("compound_events", []),
    )


def _spec_from_high(item: dict, meta: dict) -> ScenarioSpec:
    sid = item["id"]
    return ScenarioSpec(
        id=sid,
        title=item.get("title", sid.replace("_", " ").title()),
        mode=item.get("modes", ["traffic"])[0],
        complexity=item.get("complexity", "high"),
        primary_hotspots=item.get("primary_hotspots", []),
        trigger_events=item.get("trigger_events", []),
        disturbances=item.get("disturbances", {}),
        expected_subproblems=item.get("expected_subproblems", []),
        recommended_interventions=item.get("recommended_interventions", []),
        kpis=item.get("kpis", []),
        note=meta.get("note", item.get("operational_goal", "")),
        twin_hotspots=meta.get("twin_hotspots", {}),
        hotspot_dependencies=meta.get("hotspot_dependencies", {}),
        compound_events=meta.get("compound_events", []),
    )


def _spec_from_user(payload: dict) -> ScenarioSpec:
    return ScenarioSpec(**payload)


def load_scenarios() -> Dict[str, ScenarioSpec]:
    base_path, high_path, meta_path = _scenario_paths()
    base_data = _load_json(base_path, {})
    high_data = _load_json(high_path, {"scenarios": []})
    meta_data = _load_json(meta_path, {})
    user_data = _load_json(user_scenarios_path(), {})

    specs: Dict[str, ScenarioSpec] = {}
    for sid, payload in base_data.items():
        meta = meta_data.get(sid, {})
        specs[sid] = _spec_from_base(sid, payload, meta)

    for item in high_data.get("scenarios", []):
        sid = item["id"]
        meta = meta_data.get(sid, {})
        specs[sid] = _spec_from_high(item, meta)

    for sid, payload in user_data.items():
        payload = dict(payload)
        payload.setdefault("id", sid)
        specs[sid] = _spec_from_user(payload)

    return specs
