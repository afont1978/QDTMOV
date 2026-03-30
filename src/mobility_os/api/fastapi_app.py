from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from mobility_os.runtime.runtime import MobilityRuntime
from mobility_os.runtime.replay import list_replays, load_replay_bundle
from mobility_os.scenarios.loader import load_scenarios

app = FastAPI(title="QDTL2 Mobility API", version="0.3.0")
_RUNTIME_SESSIONS: Dict[str, MobilityRuntime] = {}
RUN_ROOT = Path("runs")


class StartRunRequest(BaseModel):
    scenario: str = Field(default="corridor_congestion")
    seed: int = Field(default=42)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "active_sessions": len(_RUNTIME_SESSIONS)}


@app.get("/scenarios")
def scenarios() -> Dict[str, Any]:
    items = load_scenarios()
    return {"scenarios": [{"id": s.id, "title": s.title, "mode": s.mode, "complexity": s.complexity} for s in items.values()]}


@app.get("/runs")
def runs() -> Dict[str, Any]:
    return {"runs": list_replays(RUN_ROOT)}


@app.post("/run/start")
def start_run(payload: StartRunRequest) -> Dict[str, Any]:
    runtime = MobilityRuntime(scenario=payload.scenario, seed=payload.seed, persist_root=RUN_ROOT)
    _RUNTIME_SESSIONS[runtime.run_id] = runtime
    return {"run_id": runtime.run_id, "scenario": runtime.scenario, "seed": runtime.seed}


def _get_runtime(run_id: str) -> MobilityRuntime:
    if run_id in _RUNTIME_SESSIONS:
        return _RUNTIME_SESSIONS[run_id]
    manifest = load_replay_bundle(run_id, RUN_ROOT)["manifest"]
    if not manifest:
        raise HTTPException(status_code=404, detail="run not found")
    runtime = MobilityRuntime(
        scenario=manifest.get("scenario", "corridor_congestion"),
        seed=int(manifest.get("seed", 42)),
        persist_root=RUN_ROOT,
        run_id=run_id,
        auto_persist=False,
    )
    _RUNTIME_SESSIONS[run_id] = runtime
    return runtime


@app.post("/run/{run_id}/step")
def step_run(run_id: str) -> Dict[str, Any]:
    runtime = _get_runtime(run_id)
    record = runtime.step()
    return {"run_id": run_id, "record": record.to_dict()}


@app.post("/run/{run_id}/reset")
def reset_run(run_id: str) -> Dict[str, Any]:
    runtime = _get_runtime(run_id)
    scenario = runtime.scenario
    seed = runtime.seed
    fresh = MobilityRuntime(scenario=scenario, seed=seed, persist_root=RUN_ROOT)
    _RUNTIME_SESSIONS[fresh.run_id] = fresh
    _RUNTIME_SESSIONS.pop(run_id, None)
    return {"old_run_id": run_id, "new_run_id": fresh.run_id, "scenario": scenario, "seed": seed}


@app.get("/run/{run_id}/snapshot")
def snapshot(run_id: str) -> Dict[str, Any]:
    runtime = _get_runtime(run_id)
    return {
        "run_id": run_id,
        "latest": runtime.latest_state(),
        "twins": runtime.twin_snapshot(),
    }


@app.get("/run/{run_id}/records")
def records(run_id: str) -> Dict[str, Any]:
    bundle = load_replay_bundle(run_id, RUN_ROOT)
    if not bundle["manifest"]:
        raise HTTPException(status_code=404, detail="run not found")
    return {
        "run_id": run_id,
        "manifest": bundle["manifest"],
        "records": bundle["records"].to_dict(orient="records"),
    }
