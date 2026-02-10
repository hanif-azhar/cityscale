import pandas as pd

from modules.scenario import Scenario, apply_scenario, forecast_scenarios


def _base_inputs():
    activity = pd.DataFrame(
        {
            "sector": ["residential", "transport", "industry", "waste", "energy"],
            "activity": [1000.0, 2000.0, 500.0, 200.0, 800.0],
        }
    )
    factors = pd.DataFrame(
        {
            "sector": ["residential", "transport", "industry", "waste", "energy"],
            "co2_factor": [1, 1, 1, 1, 1],
            "ch4_factor": [0, 0, 0, 0, 0],
            "n2o_factor": [0, 0, 0, 0, 0],
        }
    )
    return activity, factors


def test_apply_scenario_reduces_targeted_sectors():
    activity, factors = _base_inputs()
    scenario = Scenario(name="mit", energy_efficiency=0.1, modal_shift=0.2, renewable_share=0.3)

    out_activity, out_factors = apply_scenario(activity, factors, scenario)

    assert float(out_activity[out_activity["sector"] == "transport"]["activity"].iloc[0]) == 1600.0
    assert float(out_activity[out_activity["sector"] == "residential"]["activity"].iloc[0]) == 900.0
    assert float(out_factors[out_factors["sector"] == "energy"]["co2_factor"].iloc[0]) == 0.7


def test_forecast_scenarios_contains_baseline_comparison():
    activity, factors = _base_inputs()
    df = forecast_scenarios(
        base_activity_df=activity,
        factor_df=factors,
        population_base=1000,
        population_growth=0,
        gdp_per_capita_base=100,
        gdp_growth=0,
        start_year=2025,
        end_year=2026,
        scenarios=[Scenario(name="Baseline"), Scenario(name="Mitigation", energy_efficiency=0.2)],
    )

    assert set(df["scenario"].unique()) == {"Baseline", "Mitigation"}
    assert (df[df["scenario"] == "Baseline"]["change_vs_baseline_pct"] == 0).all()
