from __future__ import annotations

import os
from typing import Any

import pandas as pd
import streamlit as st

from mobility_os.io.hotspot_repo import load_hotspots
from mobility_os.runtime.runtime import MobilityRuntime
from mobility_os.scenarios.loader import load_scenarios
from mobility_os.ui.api_client import MobilityAPIClient
from mobility_os.ui.components import render_kpi_row
from mobility_os.ui.maps import LAYER_COLORS, hotspots_dataframe, selected_hotspot_name
from mobility_os.ui.tabs import (
    render_audit_tab,
    render_map_layers_tab,
    render_overview_tab,
    render_signals_tab,
    render_simulation_tab,
    render_storyboard_tab,
    render_twins_tab,
)


def _discover_api_base_url() -> str:
    secret_url = ''
    try:
        secret_url = str(st.secrets.get('API_BASE_URL', '')).strip()
    except Exception:
        secret_url = ''
    env_url = os.getenv('API_BASE_URL', '').strip()
    return secret_url or env_url


def _ensure_state() -> None:
    ss = st.session_state
    scenarios = load_scenarios()
    ss.setdefault('scenario', 'corridor_congestion')
    if ss['scenario'] not in scenarios:
        ss['scenario'] = next(iter(scenarios))
    ss.setdefault('seed', 42)
    ss.setdefault('running', False)
    ss.setdefault('window', 36)
    ss.setdefault('live_interval_s', 1.0)
    ss.setdefault('map_layers', list(LAYER_COLORS.keys()))
    ss.setdefault('focus_hotspot_mode', 'Auto (scenario hotspot)')
    ss.setdefault('twin_sel', 'intersection')
    ss.setdefault('api_base_url', _discover_api_base_url())
    ss.setdefault('backend_mode', 'api' if ss['api_base_url'] else 'local')
    ss.setdefault('run_id', None)
    if ss['backend_mode'] == 'local':
        ss.setdefault('rt', MobilityRuntime(ss['scenario'], ss['seed']))
    else:
        ss.setdefault('rt', None)
        if ss.get('run_id') is None and ss['api_base_url']:
            payload = MobilityAPIClient(ss['api_base_url']).start_run(ss['scenario'], int(ss['seed']))
            ss['run_id'] = payload['run_id']


def _rebuild() -> None:
    ss = st.session_state
    if ss['backend_mode'] == 'api' and ss.get('api_base_url'):
        payload = MobilityAPIClient(ss['api_base_url']).start_run(ss['scenario'], int(ss['seed']))
        ss['run_id'] = payload['run_id']
        ss['rt'] = None
    else:
        ss['rt'] = MobilityRuntime(ss['scenario'], ss['seed'])
        ss['run_id'] = None
    ss['running'] = False


def _load_view_state() -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    ss = st.session_state
    if ss['backend_mode'] == 'api' and ss.get('api_base_url') and ss.get('run_id'):
        client = MobilityAPIClient(ss['api_base_url'])
        snapshot = client.snapshot(ss['run_id'])
        records_payload = client.records(ss['run_id'])
        df = pd.DataFrame(records_payload.get('records', []))
        latest = snapshot.get('latest') or ({} if df.empty else df.iloc[-1].to_dict())
        twins = snapshot.get('twins', {})
        return df, latest, twins
    rt = ss['rt']
    df = rt.dataframe()
    latest = {} if df.empty else df.iloc[-1].to_dict()
    twins = rt.twin_snapshot()
    return df, latest, twins


def _step_once() -> None:
    ss = st.session_state
    if ss['backend_mode'] == 'api' and ss.get('api_base_url') and ss.get('run_id'):
        MobilityAPIClient(ss['api_base_url']).step(ss['run_id'])
    else:
        ss['rt'].step()


def _reset_current() -> None:
    ss = st.session_state
    if ss['backend_mode'] == 'api' and ss.get('api_base_url') and ss.get('run_id'):
        payload = MobilityAPIClient(ss['api_base_url']).reset(ss['run_id'])
        ss['run_id'] = payload['new_run_id']
        ss['rt'] = None
        ss['running'] = False
    else:
        _rebuild()


def render_app() -> None:
    st.set_page_config(page_title='Barcelona Mobility Control Room', layout='wide')

    _ensure_state()
    ss = st.session_state
    scenarios = load_scenarios()
    hotspots = load_hotspots()
    hotspots_df = hotspots_dataframe(hotspots)

    st.title('Barcelona Mobility Control Room')
    st.caption('Modular control room with local runtime or FastAPI backend mode.')

    with st.sidebar:
        st.subheader('Control panel')
        st.caption(f"Backend mode: {ss['backend_mode']}")
        if ss['backend_mode'] == 'api' and ss.get('api_base_url'):
            st.caption(f"API: {ss['api_base_url']}")
            st.caption(f"Run: {ss.get('run_id', '—')}")
        new_scenario = st.selectbox(
            'Scenario',
            list(scenarios.keys()),
            index=list(scenarios.keys()).index(ss['scenario']),
            format_func=lambda x: scenarios[x].title,
        )
        new_seed = st.number_input('Seed', min_value=1, max_value=999999, value=int(ss['seed']), step=1)
        if st.button('Apply', use_container_width=True):
            ss['scenario'] = new_scenario
            ss['seed'] = int(new_seed)
            _rebuild()
            st.rerun()

        cols = st.columns(4)
        with cols[0]:
            if st.button('Start', use_container_width=True):
                ss['running'] = True
                st.rerun()
        with cols[1]:
            if st.button('Pause', use_container_width=True):
                ss['running'] = False
                st.rerun()
        with cols[2]:
            if st.button('Step', use_container_width=True):
                _step_once()
                ss['running'] = False
                st.rerun()
        with cols[3]:
            if st.button('Reset', use_container_width=True):
                _reset_current()
                st.rerun()

        ss['window'] = st.slider('Visible window', 12, 96, int(ss['window']), step=6)
        ss['live_interval_s'] = st.slider('Live refresh interval (s)', 0.5, 3.0, float(ss['live_interval_s']), step=0.1)
        ss['map_layers'] = st.multiselect(
            'Visible map layers',
            options=list(LAYER_COLORS.keys()),
            default=ss.get('map_layers', list(LAYER_COLORS.keys())),
        )
        hotspot_options = ['Auto (scenario hotspot)'] + ([] if hotspots_df.empty else hotspots_df['name'].tolist())
        default_focus = ss.get('focus_hotspot_mode', 'Auto (scenario hotspot)')
        default_index = hotspot_options.index(default_focus) if default_focus in hotspot_options else 0
        ss['focus_hotspot_mode'] = st.selectbox('Focus hotspot', hotspot_options, index=default_index)

    run_every = f"{ss['live_interval_s']}s" if ss['running'] else None

    @st.fragment(run_every=run_every)
    def live_view() -> None:
        if st.session_state['running']:
            _step_once()

        df, latest, twins = _load_view_state()
        spec = scenarios[st.session_state['scenario']]
        focus_name = selected_hotspot_name(
            latest,
            st.session_state.get('focus_hotspot_mode', 'Auto (scenario hotspot)'),
        )

        render_kpi_row([
            ('Route', latest.get('decision_route', '—')),
            ('Network speed', f"{latest.get('network_speed_index', 0):.2f}"),
            ('Bus bunching', f"{latest.get('bus_bunching_index', 0):.2f}"),
            ('Risk', f"{latest.get('risk_score', 0):.2f}"),
            ('Gateway delay', f"{latest.get('gateway_delay_index', 0):.2f}"),
        ])

        tabs = st.tabs([
            'Overview',
            'Map & Layers',
            'Signals & Alerts Map',
            'Scenario Storyboard',
            'Mobility Twins',
            'What-if & Simulation',
            'Audit & Orchestration',
        ])

        with tabs[0]:
            render_overview_tab(
                df, latest, spec, hotspots_df, focus_name,
                int(st.session_state['window']),
                st.session_state.get('map_layers', list(LAYER_COLORS.keys())),
            )
        with tabs[1]:
            render_map_layers_tab(
                df, latest, hotspots_df, focus_name,
                st.session_state.get('map_layers', list(LAYER_COLORS.keys())),
            )
        with tabs[2]:
            render_signals_tab(df, latest, hotspots_df, focus_name, int(st.session_state['window']))
        with tabs[3]:
            render_storyboard_tab(df, latest, spec, hotspots_df, focus_name)
        with tabs[4]:
            render_twins_tab(df, latest, hotspots_df, twins, int(st.session_state['window']))
        with tabs[5]:
            render_simulation_tab(df, latest, hotspots_df, focus_name)
        with tabs[6]:
            render_audit_tab(df, hotspots_df)

    live_view()
