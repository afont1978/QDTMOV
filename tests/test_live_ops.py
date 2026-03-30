from mobility_os.runtime.live_ops import should_auto_pause


def test_auto_pause_on_critical_risk():
    pause, message = should_auto_pause({"risk_score": 0.9, "gateway_delay_index": 0.2, "bus_bunching_index": 0.1, "active_event": "none"})
    assert pause is True
    assert "critical safety risk" in message.lower()


def test_no_auto_pause_in_normal_conditions():
    pause, message = should_auto_pause({"risk_score": 0.3, "gateway_delay_index": 0.3, "bus_bunching_index": 0.2, "active_event": "none"})
    assert pause is False
    assert message == ""
