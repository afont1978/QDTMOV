from mobility_os.scenarios.editor import (
    apply_demo_preset,
    apply_domain_template,
    apply_shocks,
    save_custom_scenario,
    scenario_to_editor_dict,
)
from mobility_os.scenarios.loader import load_scenarios


def test_can_save_and_load_custom_scenario(monkeypatch, tmp_path):
    custom_path = tmp_path / "user_scenarios.json"
    monkeypatch.setenv("QDTMOV_USER_SCENARIOS_PATH", str(custom_path))

    scenarios = load_scenarios()
    base = scenarios["corridor_congestion"]

    payload = scenario_to_editor_dict(base)
    payload["id"] = "corridor_congestion_custom_test"
    payload["title"] = "Corridor congestion custom test"
    payload["primary_hotspots"] = payload["primary_hotspots"][:1] or ["Plaça de les Glòries Catalanes"]
    payload["disturbances"] = {"corridor_flow_multiplier": 1.12}
    payload["trigger_events"] = ["demand_spike"]

    path = save_custom_scenario(payload)
    assert path.exists()

    loaded = load_scenarios()
    assert "corridor_congestion_custom_test" in loaded
    assert loaded["corridor_congestion_custom_test"].title == "Corridor congestion custom test"
    assert loaded["corridor_congestion_custom_test"].disturbances["corridor_flow_multiplier"] == 1.12


def test_templates_and_shocks_enrich_payload():
    scenarios = load_scenarios()
    base = scenario_to_editor_dict(scenarios["corridor_congestion"])

    templated = apply_domain_template(base, "gateway_access")
    assert templated["mode"] == "gateway"
    assert "gateway_surge" in templated["trigger_events"]

    shocked = apply_shocks(base, ["rain_shock", "incident_chain"])
    assert "rain_event" in shocked["trigger_events"]
    assert "incident" in shocked["trigger_events"]
    assert "visibility" in shocked["disturbances"]

    demo = apply_demo_preset(base, "wet_school_safety_demo")
    assert demo["mode"] == "safety"
    assert "school_peak" in demo["trigger_events"]
