from __future__ import annotations

import pandas as pd
import plotly.express as px


def sector_bar_chart(sector_df: pd.DataFrame):
    return px.bar(
        sector_df,
        x="sector",
        y="co2e",
        color="sector",
        title="Sector Emissions (CO2e)",
        labels={"co2e": "CO2e", "sector": "Sector"},
    )


def scenario_line_chart(forecast_df: pd.DataFrame):
    return px.line(
        forecast_df,
        x="year",
        y="total_co2e",
        color="scenario",
        title="Scenario Forecast: Total Emissions",
        labels={"total_co2e": "CO2e", "year": "Year"},
    )


def intensity_line_chart(forecast_df: pd.DataFrame, metric: str = "per_capita_co2e"):
    title_map = {
        "per_capita_co2e": "Per Capita Emissions",
        "per_gdp_co2e": "Emissions Intensity per GDP",
    }
    return px.line(
        forecast_df,
        x="year",
        y=metric,
        color="scenario",
        title=title_map.get(metric, metric),
    )


def baseline_comparison_chart(forecast_df: pd.DataFrame):
    return px.bar(
        forecast_df,
        x="year",
        y="change_vs_baseline_pct",
        color="scenario",
        barmode="group",
        title="Relative Change vs Baseline (%)",
    )
