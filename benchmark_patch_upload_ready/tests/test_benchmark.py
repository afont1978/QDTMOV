
from mobility_os.runtime.benchmark import aggregate_benchmark, benchmark_runs, best_seed_per_scenario


def test_benchmark_runs():
    df = benchmark_runs(["corridor_congestion"], [42], steps=4)
    assert len(df) == 1
    assert "avg_operational_score" in df.columns
    assert "final_operational_score" in df.columns


def test_benchmark_aggregates():
    df = benchmark_runs(["corridor_congestion", "urban_logistics_saturation"], [11, 22], steps=4)
    summary = aggregate_benchmark(df)
    best = best_seed_per_scenario(df)
    assert not summary.empty
    assert set(["scenario", "runs", "avg_exec_ms"]).issubset(summary.columns)
    assert not best.empty
    assert "seed" in best.columns
