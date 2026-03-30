from mobility_os.runtime.explainability import explain_route_decision, objective_breakdown_df, trigger_signals_df


def test_explainability_helpers_build_expected_outputs():
    row = {
        "decision_route": "QUANTUM",
        "route_reason": "Quantum selected because the step combines multiple discrete urban control actions.",
        "decision_confidence": 0.82,
        "fallback_triggered": False,
        "latency_breach": False,
        "fallback_reasons": [],
        "risk_score": 0.61,
        "bus_bunching_index": 0.35,
        "gateway_delay_index": 0.20,
        "curb_occupancy_rate": 0.80,
        "illegal_curb_occupancy_rate": 0.10,
        "complexity_score": 5.2,
        "discrete_ratio": 0.55,
        "objective_breakdown_json": '{"risk_penalty": 7.5, "delay_penalty": 4.0}',
        "result_json": '{"backend": {"provider": "SIM_QPU", "backend_id": "sim-mobility-qpu", "queue_ms": 320, "exec_ms": 180}}',
        "qre_json": '{"mode": "traffic", "scenario": "corridor_congestion"}',
    }
    explanation = explain_route_decision(row)
    breakdown = objective_breakdown_df(row)
    signals = trigger_signals_df(row)

    assert explanation["route"] == "QUANTUM"
    assert explanation["confidence_band"] == "Medium"
    assert explanation["backend_provider"] == "SIM_QPU"
    assert not breakdown.empty
    assert "Risk score" in signals["Signal"].tolist()
    assert len(explanation["dominant_factors"]) >= 1
