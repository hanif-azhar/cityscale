from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from .emissions_engine import aggregate_emissions, compute_sector_emissions
from .urban_form import apply_urban_form_modifiers
from .utils import clamp, year_range


@dataclass
class Scenario:
    name: str
    energy_efficiency: float = 0.0
    renewable_share: float = 0.0
    modal_shift: float = 0.0
    industry_efficiency: float = 0.0
    waste_reduction: float = 0.0

    def normalized(self) -> "Scenario":
        return Scenario(
            name=self.name,
            energy_efficiency=clamp(self.energy_efficiency),
            renewable_share=clamp(self.renewable_share),
            modal_shift=clamp(self.modal_shift),
            industry_efficiency=clamp(self.industry_efficiency),
            waste_reduction=clamp(self.waste_reduction),
        )


def apply_scenario(activity_df: pd.DataFrame, factor_df: pd.DataFrame, scenario: Scenario) -> tuple[pd.DataFrame, pd.DataFrame]:
    scn = scenario.normalized()
    adjusted_activity = activity_df.copy()
    adjusted_factors = factor_df.copy()
    adjusted_factors[["co2_factor", "ch4_factor", "n2o_factor"]] = adjusted_factors[
        ["co2_factor", "ch4_factor", "n2o_factor"]
    ].astype(float)

    adjustments = {
        "residential": (1 - scn.energy_efficiency),
        "energy": (1 - scn.energy_efficiency),
        "transport": (1 - scn.modal_shift),
        "industry": (1 - scn.industry_efficiency),
        "waste": (1 - scn.waste_reduction),
    }

    for sector, mult in adjustments.items():
        mask = adjusted_activity["sector"] == sector
        if mask.any():
            adjusted_activity.loc[mask, "activity"] = adjusted_activity.loc[mask, "activity"] * mult

    if "energy" in adjusted_factors["sector"].values:
        mask = adjusted_factors["sector"] == "energy"
        adjusted_factors.loc[mask, ["co2_factor", "ch4_factor", "n2o_factor"]] = (
            adjusted_factors.loc[mask, ["co2_factor", "ch4_factor", "n2o_factor"]] * (1 - scn.renewable_share)
        )

    return adjusted_activity, adjusted_factors


def forecast_scenarios(
    base_activity_df: pd.DataFrame,
    factor_df: pd.DataFrame,
    population_base: float,
    population_growth: float,
    gdp_per_capita_base: float,
    gdp_growth: float,
    start_year: int,
    end_year: int,
    scenarios: Iterable[Scenario],
    urban_modifiers: dict[str, float] | None = None,
) -> pd.DataFrame:
    records: list[dict] = []

    for scenario in scenarios:
        for year in year_range(start_year, end_year):
            t = year - start_year
            population = population_base * ((1 + population_growth) ** t)
            gdp_per_capita = gdp_per_capita_base * ((1 + gdp_growth) ** t)
            gdp = population * gdp_per_capita

            scaled = base_activity_df.copy()
            pop_scale = ((1 + population_growth) ** t)
            gdp_scale = ((1 + gdp_growth) ** t)

            scaled.loc[scaled["sector"].isin(["residential", "transport", "waste"]), "activity"] *= pop_scale
            scaled.loc[scaled["sector"].isin(["industry", "energy"]), "activity"] *= ((pop_scale + gdp_scale) / 2)

            if urban_modifiers:
                scaled = apply_urban_form_modifiers(scaled, urban_modifiers)

            adj_activity, adj_factors = apply_scenario(scaled, factor_df, scenario)
            sector = compute_sector_emissions(adj_activity, adj_factors)
            summary = aggregate_emissions(sector, population=population, gdp=gdp)

            records.append(
                {
                    "year": year,
                    "scenario": scenario.name,
                    "total_co2e": summary["total_co2e"],
                    "per_capita_co2e": summary["per_capita_co2e"],
                    "per_gdp_co2e": summary["per_gdp_co2e"],
                    "population": population,
                    "gdp": gdp,
                }
            )

    df = pd.DataFrame(records)
    baseline = df[df["scenario"].str.lower() == "baseline"][["year", "total_co2e"]].rename(
        columns={"total_co2e": "baseline_total"}
    )
    merged = df.merge(baseline, on="year", how="left")
    merged["change_vs_baseline_pct"] = ((merged["total_co2e"] - merged["baseline_total"]) / merged["baseline_total"]) * 100
    merged.loc[merged["scenario"].str.lower() == "baseline", "change_vs_baseline_pct"] = 0.0
    return merged
