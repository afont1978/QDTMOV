from __future__ import annotations

import json

import streamlit as st

from mobility_os.scenarios.editor import (
    save_custom_scenario,
    scenario_to_editor_dict,
    sanitize_scenario_id,
    validate_editor_payload,
)
from mobility_os.scenarios.loader import load_scenarios


def _csv_list(value: str) -> list[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


def _json_dict(value: str) -> dict:
    value = value.strip()
    if not value:
        return {}
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("JSON value must be an object.")
    return parsed


def render_scenario_editor_tab() -> None:
    st.subheader("Scenario Editor")
    scenarios = load_scenarios()
    base_id = st.selectbox(
        "Base scenario",
        list(scenarios.keys()),
        format_func=lambda x: scenarios[x].title,
        key="scenario_editor_base_id",
    )
    base = scenario_to_editor_dict(scenarios[base_id])

    with st.form("scenario_editor_form"):
        scenario_id = st.text_input("Scenario id", value=f"{base['id']}_custom")
        title = st.text_input("Title", value=f"{base['title']} (Custom)")
        mode = st.selectbox(
            "Mode",
            ["traffic", "safety", "logistics", "gateway", "event", "transit"],
            index=["traffic", "safety", "logistics", "gateway", "event", "transit"].index(base["mode"]) if base["mode"] in ["traffic", "safety", "logistics", "gateway", "event", "transit"] else 0,
        )
        complexity = st.selectbox(
            "Complexity",
            ["low", "medium", "high", "very_high", "extreme"],
            index=["low", "medium", "high", "very_high", "extreme"].index(base["complexity"]) if base["complexity"] in ["low", "medium", "high", "very_high", "extreme"] else 1,
        )
        primary_hotspots = st.text_area("Primary hotspots (comma-separated)", value=", ".join(base["primary_hotspots"]), height=100)
        trigger_events = st.text_area("Trigger events (comma-separated)", value=", ".join(base["trigger_events"]), height=80)
        expected_subproblems = st.text_area("Expected subproblems (comma-separated)", value=", ".join(base["expected_subproblems"]), height=80)
        recommended_interventions = st.text_area("Recommended interventions (comma-separated)", value=", ".join(base["recommended_interventions"]), height=80)
        kpis = st.text_area("KPIs (comma-separated)", value=", ".join(base["kpis"]), height=80)
        note = st.text_area("Operational note", value=base["note"], height=120)
        disturbances_text = st.text_area(
            "Disturbances JSON",
            value=json.dumps(base["disturbances"], ensure_ascii=False, indent=2),
            height=220,
        )
        twin_hotspots_text = st.text_area(
            "Twin hotspots JSON",
            value=json.dumps(base["twin_hotspots"], ensure_ascii=False, indent=2),
            height=220,
        )
        submitted = st.form_submit_button("Save as new scenario", use_container_width=True)

    payload = {
        "id": sanitize_scenario_id(scenario_id),
        "title": title,
        "mode": mode,
        "complexity": complexity,
        "primary_hotspots": _csv_list(primary_hotspots),
        "trigger_events": _csv_list(trigger_events),
        "expected_subproblems": _csv_list(expected_subproblems),
        "recommended_interventions": _csv_list(recommended_interventions),
        "kpis": _csv_list(kpis),
        "note": note,
    }

    json_errors = []
    try:
        payload["disturbances"] = _json_dict(disturbances_text)
    except Exception as exc:
        json_errors.append(f"Disturbances JSON is invalid: {exc}")
        payload["disturbances"] = {}
    try:
        payload["twin_hotspots"] = _json_dict(twin_hotspots_text)
    except Exception as exc:
        json_errors.append(f"Twin hotspots JSON is invalid: {exc}")
        payload["twin_hotspots"] = {}

    errors = validate_editor_payload(payload) + json_errors

    st.markdown("### Preview")
    st.code(json.dumps(payload, ensure_ascii=False, indent=2), language="json")

    if errors:
        for err in errors:
            st.error(err)
    else:
        st.success("Scenario payload is valid.")

    if submitted:
        if errors:
            st.error("Cannot save scenario until all validation errors are resolved.")
        else:
            path = save_custom_scenario(payload)
            st.success(f"Scenario saved in {path}.")
            st.info("Use the sidebar Scenario selector after rerun to test the new scenario.")
            st.rerun()
