from __future__ import annotations

from typing import Dict

import pandas as pd

from .utils import DEFAULT_GWP, safe_divide

REQUIRED_ACTIVITY_COLUMNS = {"sector", "activity"}
REQUIRED_FACTOR_COLUMNS = {"sector", "co2_factor", "ch4_factor", "n2o_factor"}


def _check_required(df: pd.DataFrame, required: set[str], name: str) -> None:
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")


def compute_sector_emissions(
    activity_df: pd.DataFrame,
    factor_df: pd.DataFrame,
    gwp: Dict[str, float] | None = None,
) -> pd.DataFrame:
    _check_required(activity_df, REQUIRED_ACTIVITY_COLUMNS, "activity_df")
    _check_required(factor_df, REQUIRED_FACTOR_COLUMNS, "factor_df")

    gwp_values = {**DEFAULT_GWP, **(gwp or {})}

    merged = activity_df.merge(factor_df, how="left", on="sector")
    if merged[["co2_factor", "ch4_factor", "n2o_factor"]].isna().any().any():
        missing_sectors = merged[merged["co2_factor"].isna()]["sector"].tolist()
        raise ValueError(f"Missing emission factors for sectors: {missing_sectors}")

    merged = merged.copy()
    merged["co2"] = merged["activity"] * merged["co2_factor"]
    merged["ch4"] = merged["activity"] * merged["ch4_factor"]
    merged["n2o"] = merged["activity"] * merged["n2o_factor"]
    merged["co2e"] = (
        merged["co2"]
        + (merged["ch4"] * gwp_values["CH4"])
        + (merged["n2o"] * gwp_values["N2O"])
    )

    return merged[["sector", "activity", "co2", "ch4", "n2o", "co2e"]].sort_values("co2e", ascending=False)


def aggregate_emissions(
    sector_emissions: pd.DataFrame,
    population: float,
    gdp: float,
) -> dict[str, float]:
    total = float(sector_emissions["co2e"].sum())
    return {
        "total_co2e": total,
        "per_capita_co2e": safe_divide(total, population),
        "per_gdp_co2e": safe_divide(total, gdp),
    }
