
from mobility_os.runtime.runtime import MobilityRuntime
from mobility_os.runtime.replay import summarize_run, compare_runs, build_replay_frame
from mobility_os.io.run_store import RunStore


def test_replay_summary_and_compare(tmp_path):
    rt_a = MobilityRuntime("corridor_congestion", seed=42, persist_root=tmp_path / "runs_a")
    rt_b = MobilityRuntime("corridor_congestion", seed=43, persist_root=tmp_path / "runs_b")
    for _ in range(4):
        rt_a.step()
        rt_b.step()

    df_a = rt_a.dataframe()
    df_b = rt_b.dataframe()

    summary = summarize_run(df_a)
    assert summary["steps"] == 4
    assert "score_mean" in summary

    frame = build_replay_frame(df_a, 2)
    assert frame["row"]["step_id"] == 3

    compare_df = compare_runs(df_a, df_b, "A", "B")
    assert not compare_df.empty
    assert "Metric" in compare_df.columns


def test_run_store_load_and_export(tmp_path):
    store = RunStore(tmp_path / "runs")
    rid = store.create_run({"scenario": "corridor_congestion", "title": "Test run"})
    store.append_record(rid, {"step_id": 1, "scenario": "corridor_congestion"})
    bundle = store.load_run(rid)
    assert bundle["manifest"]["run_id"] == rid
    assert len(bundle["records"]) == 1
    csv_bytes = store.export_run_csv_bytes(rid)
    assert b"step_id" in csv_bytes
