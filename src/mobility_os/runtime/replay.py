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
    store = RunStore(root)
    return {
        "manifest": store.read_manifest(run_id) or {},
        "records": store.read_records(run_id),
    }
