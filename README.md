# QDTL2 — Barcelona Mobility Control Room

Refactored repository for a hybrid classical–quantum urban mobility control room focused on Barcelona.

## Included

- Modular package layout under `src/mobility_os/`
- Streamlit dashboard entrypoint in `app.py`
- Compatibility wrapper in `mobility_runtime.py`
- Synthetic mobility runtime with:
  - scenario-driven execution
  - hybrid route selection
  - fallback-to-classical logic
  - replay-ready persisted runs
- Scenario libraries under `data/scenarios/`
- Hotspot catalogue under `data/hotspots/`
- FastAPI service under `src/mobility_os/api/fastapi_app.py`
- Basic automated tests

## Repository structure

```text
qdtl2/
├─ app.py
├─ mobility_runtime.py
├─ pyproject.toml
├─ requirements.txt
├─ Makefile
├─ data/
│  ├─ hotspots/
│  └─ scenarios/
├─ src/
│  └─ mobility_os/
│     ├─ api/
│     ├─ domain/
│     ├─ io/
│     ├─ orchestration/
│     ├─ runtime/
│     ├─ scenarios/
│     ├─ solvers/
│     └─ ui/
└─ tests/
```

## Run locally

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Launch the dashboard:

```bash
python -m streamlit run app.py
```

Run tests:

```bash
python -m pytest -q
```

Launch the API:

```bash
python -m uvicorn mobility_os.api.fastapi_app:app --app-dir src --reload
```

## API endpoints

- `GET /health`
- `GET /scenarios`
- `GET /runs`
- `POST /run/start`
- `POST /run/{run_id}/step`
- `POST /run/{run_id}/reset`
- `GET /run/{run_id}/snapshot`
- `GET /run/{run_id}/records`

## Notes

This repository is a complete, modularized refactor base. It preserves the original project intent and core concepts while separating the system into reusable packages for runtime, orchestration, UI, scenarios, persistence and API.

The dashboard is fully mounted as a coherent repo, but it is still a pragmatic refactor base rather than a perfect one-to-one recreation of every visual nuance from the original monolithic app.
