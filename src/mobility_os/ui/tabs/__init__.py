from __future__ import annotations

import streamlit as st

from .overview import render_overview_tab
from .map_layers import render_map_layers_tab
from .signals import render_signals_tab
from .storyboard import render_storyboard_tab
from .simulation import render_simulation_tab
from .twins import render_twins_tab
from .audit import render_audit_tab
from .benchmark import render_benchmark_tab

try:
    from .replay import render_replay_tab
except Exception:
    def render_replay_tab() -> None:
        st.info("Replay & Runs tab not available in this deployment yet.")


__all__ = [
    "render_overview_tab",
    "render_map_layers_tab",
    "render_signals_tab",
    "render_storyboard_tab",
    "render_simulation_tab",
    "render_twins_tab",
    "render_audit_tab",
    "render_benchmark_tab",
    "render_replay_tab",
]
