from __future__ import annotations

from typing import Any, Dict

import httpx


class MobilityAPIClient:
    def __init__(self, base_url: str, timeout: float = 20.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _get(self, path: str) -> Dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(self._url(path))
            response.raise_for_status()
            return response.json()

    def _post(self, path: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(self._url(path), json=payload or {})
            response.raise_for_status()
            return response.json()

    def health(self) -> Dict[str, Any]:
        return self._get('/health')

    def scenarios(self) -> Dict[str, Any]:
        return self._get('/scenarios')

    def runs(self) -> Dict[str, Any]:
        return self._get('/runs')

    def start_run(self, scenario: str, seed: int) -> Dict[str, Any]:
        return self._post('/run/start', {'scenario': scenario, 'seed': int(seed)})

    def step(self, run_id: str) -> Dict[str, Any]:
        return self._post(f'/run/{run_id}/step')

    def reset(self, run_id: str) -> Dict[str, Any]:
        return self._post(f'/run/{run_id}/reset')

    def snapshot(self, run_id: str) -> Dict[str, Any]:
        return self._get(f'/run/{run_id}/snapshot')

    def records(self, run_id: str) -> Dict[str, Any]:
        return self._get(f'/run/{run_id}/records')
