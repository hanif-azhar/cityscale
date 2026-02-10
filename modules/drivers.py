from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pandas as pd


@dataclass
class PopulationDriver:
    initial_population: float
    annual_growth_rate: float

    def value_at(self, years_from_base: int) -> float:
        return self.initial_population * ((1 + self.annual_growth_rate) ** years_from_base)


@dataclass
class EconomicDriver:
    gdp_per_capita: float
    gdp_growth_rate: float
    energy_intensity: float

    def gdp_per_capita_at(self, years_from_base: int) -> float:
        return self.gdp_per_capita * ((1 + self.gdp_growth_rate) ** years_from_base)


@dataclass
class SectorActivity:
    residential_energy: float
    transport_activity: float
    industrial_output: float
    waste_activity: float
    grid_energy: float

    def to_activity_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "sector": ["residential", "transport", "industry", "waste", "energy"],
                "activity": [
                    self.residential_energy,
                    self.transport_activity,
                    self.industrial_output,
                    self.waste_activity,
                    self.grid_energy,
                ],
            }
        )


@dataclass
class CityStatistics:
    city_name: str
    population_driver: PopulationDriver
    economic_driver: EconomicDriver
    sector_activity: SectorActivity

    def to_base_dict(self) -> Dict[str, float | str]:
        return {
            "city_name": self.city_name,
            "population": self.population_driver.initial_population,
            "population_growth": self.population_driver.annual_growth_rate,
            "gdp_per_capita": self.economic_driver.gdp_per_capita,
            "gdp_growth": self.economic_driver.gdp_growth_rate,
            "energy_intensity": self.economic_driver.energy_intensity,
        }

    def to_projection_frame(self, years: list[int], base_year: int) -> pd.DataFrame:
        rows = []
        for year in years:
            dt = year - base_year
            pop = self.population_driver.value_at(dt)
            gdp_pc = self.economic_driver.gdp_per_capita_at(dt)
            rows.append(
                {
                    "year": year,
                    "population": pop,
                    "gdp_per_capita": gdp_pc,
                    "gdp": pop * gdp_pc,
                    "energy_intensity": self.economic_driver.energy_intensity,
                }
            )
        return pd.DataFrame(rows)


def synthetic_city_dataset() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sector": ["residential", "transport", "industry", "waste", "energy"],
            "activity": [1200000, 800000000, 450000, 180000, 2300000],
        }
    )
