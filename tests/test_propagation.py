from mobility_os.runtime.runtime import MobilityRuntime
from mobility_os.runtime.explainability import active_hotspots_df, impact_chain_df


def test_runtime_generates_propagation_payloads():
    rt = MobilityRuntime(scenario="gateway_access_stress", seed=42, persist_root=None, auto_persist=False)
    record = rt.step()
    row = record.to_dict()

    assert row["hotspot_count"] >= 1
    assert row["network_cascade_score"] >= 0.0
    active_df = active_hotspots_df(row)
    chain_df = impact_chain_df(row)

    assert not active_df.empty
    assert "severity" in active_df.columns
    assert "name" in active_df.columns
    assert chain_df is not None
