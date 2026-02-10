import pandas as pd

from modules.emissions_engine import aggregate_emissions, compute_sector_emissions


def test_compute_sector_emissions_includes_gwp_scaling():
    activity = pd.DataFrame({"sector": ["residential"], "activity": [100.0]})
    factors = pd.DataFrame(
        {
            "sector": ["residential"],
            "co2_factor": [1.0],
            "ch4_factor": [0.1],
            "n2o_factor": [0.01],
        }
    )

    result = compute_sector_emissions(activity, factors)
    co2e = result.iloc[0]["co2e"]

    expected = 100.0 + (10.0 * 28.0) + (1.0 * 265.0)
    assert abs(co2e - expected) < 1e-9


def test_aggregate_emissions_metrics():
    sector = pd.DataFrame({"sector": ["a", "b"], "co2e": [100.0, 300.0]})
    summary = aggregate_emissions(sector, population=200.0, gdp=1000.0)

    assert summary["total_co2e"] == 400.0
    assert summary["per_capita_co2e"] == 2.0
    assert summary["per_gdp_co2e"] == 0.4
