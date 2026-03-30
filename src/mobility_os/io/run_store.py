
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import pandas as pd


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_runs_root(root: str | Path | None = None) -> Path:
    if root:
        p = Path(root)
    else:
        env_dir = os.getenv("QDTMOV_RUNS_DIR")
        if env_dir:
            p = Path(env_dir)
        else:
            p = Path(tempfile.gettempdir()) / "qdtmov_runs"
    p.mkdir(parents=True, exist_ok=True)
    return p


class RunStore:
    def __init__(self, root: str | Path | None = None):
        self.root = resolve_runs_root(root)

    def create_run(self, metadata: Dict[str, Any], run_id: Optional[str] = None) -> str:
        rid = run_id or uuid4().hex[:12]
        run_dir = self.root / rid
        run_dir.mkdir(parents=True, exist_ok=True)
        manifest = dict(metadata)
        manifest.setdefault("run_id", rid)
        manifest.setdefault("created_at", utc_now_iso())
        manifest.setdefault("updated_at", manifest["created_at"])
        manifest.setdefault("records", 0)
        (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        (run_dir / "records.jsonl").touch()
        return rid

    def append_record(self, run_id: str, record: Dict[str, Any]) -> None:
        run_dir = self.root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        with (run_dir / "records.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        manifest = self.read_manifest(run_id) or {"run_id": run_id, "created_at": utc_now_iso(), "records": 0}
        manifest["updated_at"] = utc_now_iso()
        manifest["records"] = int(manifest.get("records", 0)) + 1
        (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    def save_run_metadata(self, run_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        manifest = self.read_manifest(run_id) or {"run_id": run_id, "created_at": utc_now_iso(), "records": 0}
        manifest.update(updates or {})
        manifest["updated_at"] = utc_now_iso()
        run_dir = self.root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return manifest

    def read_manifest(self, run_id: str) -> Dict[str, Any] | None:
        path = self.root / run_id / "manifest.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def read_records(self, run_id: str) -> pd.DataFrame:
        path = self.root / run_id / "records.jsonl"
        if not path.exists() or path.stat().st_size == 0:
            return pd.DataFrame()
        rows: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        return pd.DataFrame(rows)

    def load_run(self, run_id: str) -> Dict[str, Any]:
        return {
            "manifest": self.read_manifest(run_id) or {},
            "records": self.read_records(run_id),
        }

    def export_run_csv_bytes(self, run_id: str) -> bytes:
        df = self.read_records(run_id)
        if df.empty:
            return b""
        return df.to_csv(index=False).encode("utf-8")

    def list_runs(self) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for manifest_path in self.root.glob("*/manifest.json"):
            try:
                rows.append(json.loads(manifest_path.read_text(encoding="utf-8")))
            except Exception:
                continue
        def _sort_key(item: Dict[str, Any]) -> str:
            return str(item.get("updated_at") or item.get("created_at") or "")
        rows.sort(key=_sort_key, reverse=True)
        return rows
