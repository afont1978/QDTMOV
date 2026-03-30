from __future__ import annotations

import json

import streamlit as st

from mobility_os.scenarios.editor import (
    apply_demo_preset,
    apply_domain_template,
    apply_shocks,
    save_custom_scenario,
    scenario_to_editor_dict,
    sanitize_scenario_id,
    validate_editor_payload,
)
from mobility_os.scenarios.loader import load_scenarios
from mobility_os.scenarios.presets import DEMO_PRESETS, DOMAIN_TEMPLATES, SHOCK_LIBRARY


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

    top = st.columns(3)
    with top[0]:
        base_id = st.selectbox(
            "Base scenario",
            list(scenarios.keys()),
            format_func=lambda x: scenarios[x].title,
            key="scenario_editor_base_id",
        )
    with top[1]:
        template_id = st.selectbox(
            "Domain template",
            list(DOMAIN_TEMPLATES.keys()),
            format_func=lambda x: DOMAIN_TEMPLATES[x]["label"],
            key="scenario_editor_template_id",
        )
    with top[2]:
        preset_id = st.selectbox(
            "Demo preset",
            list(DEMO_PRESETS.keys()),
            format_func=lambda x: DEMO_PRESETS[x]["label"],
            key="scenario_editor_preset_id",
        )

    shock_ids = st.multiselect(
        "Shock library",
        list(SHOCK_LIBRARY.keys()),
        default=list(DEMO_PRESETS.get(preset_id, {}).get("shocks", [])),
        format_func=lambda x: SHOCK_LIBRARY[x]["label"],
        key="scenario_editor_shock_ids",
    )

    base = scenario_to_editor_dict(scenarios[base_id])
    working = apply_domain_template(base, template_id)
    working = apply_demo_preset(working, preset_id)
    working = apply_shocks(working, shock_ids)

    id_suffix_parts = [p for p in [template_id if template_id != "none" else "", preset_id if preset_id != "none" else ""] if p]
    suggested_suffix = "_".join(id_suffix_parts) if id_suffix_parts else "custom"

    with st.form("scenario_editor_form"):
        scenario_id = st.text_input("Scenario id", value=f"{base['id']}_{suggested_suffix}")
        title = st.text_input("Title", value=f"{working['title']} ({suggested_suffix.replace('_', ' ').title()})")
        mode = st.selectbox(
            "Mode",
            ["traffic", "safety", "logistics", "gateway", "event", "transit"],
            index=["traffic", "safety", "logistics", "gateway", "event", "transit"].index(working["mode"]) if working["mode"] in ["traffic", "safety", "logistics", "gateway", "event", "transit"] else 0,
        )
        complexity = st.selectbox(
            "Complexity",
            ["low", "medium", "high", "very_high", "extreme"],
            index=["low", "medium", "high", "very_high", "extreme"].index(working["complexity"]) if working["complexity"] in ["low", "medium", "high", "very_high", "extreme"] else 1,
        )
        primary_hotspots = st.text_area("Primary hotspots (comma-separated)", value=", ".join(working["primary_hotspots"]), height=100)
        trigger_events = st.text_area("Trigger events (comma-separated)", value=", ".join(working["trigger_events"]), height=80)
        expected_subproblems = st.text_area("Expected subproblems (comma-separated)", value=", ".join(working["expected_subproblems"]), height=80)
        recommended_interventions = st.text_area("Recommended interventions (comma-separated)", value=", ".join(working["recommended_interventions"]), height=80)
        kpis = st.text_area("KPIs (comma-separated)", value=", ".join(working["kpis"]), height=80)
        note = st.text_area("Operational note", value=working["note"], height=120)
        disturbances_text = st.text_area(
            "Disturbances JSON",
            value=json.dumps(working["disturbances"], ensure_ascii=False, indent=2),
            height=220,
        )
        twin_hotspots_text = st.text_area(
            "Twin hotspots JSON",
            value=json.dumps(working["twin_hotspots"], ensure_ascii=False, indent=2),
            height=220,
        )
        submitted = st.form_submit_button("Save as new scenario", use_container_width=True)

    st.caption("Available quick presets:")
    preset_cols = st.columns(3)
    preset_items = list(DEMO_PRESETS.items())
    for col, (pid, info) in zip(preset_cols * ((len(preset_items) // 3) + 1), preset_items):
        with col:
            st.markdown(f"**{info['label']}**")
            st.caption(f"Template: {info.get('template', 'none')} | Shocks: {', '.join(info.get('shocks', [])) or 'none'}")

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

    left, right = st.columns([1.1, 0.9])
    with left:
        st.markdown("### Preview")
        st.code(json.dumps(payload, ensure_ascii=False, indent=2), language="json")
    with right:
        st.markdown("### Active modifiers")
        st.write(f"Template: {DOMAIN_TEMPLATES[template_id]['label']}")
        st.write(f"Demo preset: {DEMO_PRESETS[preset_id]['label']}")
        st.write("Shocks:")
        st.write([SHOCK_LIBRARY[x]["label"] for x in shock_ids] if shock_ids else ["None"])

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
