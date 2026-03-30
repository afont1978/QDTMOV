from mobility_os.runtime.executive import executive_snapshot, pressure_ranking_df, subsystem_scores_df, trend_table
from mobility_os.runtime.runtime import MobilityRuntime


def test_executive_helpers_return_expected_structures():
    rt = MobilityRuntime("corridor_congestion", 42)
    for _ in range(5):
        rt.step()
    df = rt.dataframe()
    latest = df.iloc[-1].to_dict()

    snapshot = executive_snapshot(df)
    subsystems = subsystem_scores_df(latest)
    pressure = pressure_ranking_df(latest)
    trends = trend_table(df)

    assert "city_score" in snapshot
    assert snapshot["city_status"] in {"Green", "Amber", "Red"}
    assert not subsystems.empty
    assert set(subsystems["Subsystem"].tolist()) == {"Traffic", "Transit", "Risk", "Logistics", "Gateway"}
    assert not pressure.empty
    assert "Δ15" in trends.columns
