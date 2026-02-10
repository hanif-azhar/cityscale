from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from modules.emissions_engine import aggregate_emissions, compute_sector_emissions
from modules.io_handlers import (
    load_activity_data,
    load_factor_data,
    manual_input_to_activity,
    validate_activity_data,
    validate_factor_data,
)
from modules.report_export import export_excel_report, export_pdf_report
from modules.scenario import Scenario, forecast_scenarios
from modules.storage import list_runs, load_run, save_run
from modules.urban_form import UrbanFormParameters, calculate_urban_modifiers
from modules.visualization import (
    baseline_comparison_chart,
    intensity_line_chart,
    scenario_line_chart,
    sector_bar_chart,
)

st.set_page_config(page_title="CityScale - Urban Emissions Simulator", layout="wide")

DATA_DIR = Path(__file__).parent / "data"
RUN_DIR = Path(__file__).parent / "runs"
DEFAULT_FACTORS = DATA_DIR / "emission_factors.csv"


def _load_default_factors() -> pd.DataFrame:
    return pd.read_csv(DEFAULT_FACTORS)


def _manual_input_panel() -> tuple[pd.DataFrame, dict]:
    col1, col2 = st.columns(2)
    with col1:
        city_name = st.text_input("City Name", "Sample City")
        population = st.number_input("Population", min_value=0.0, value=1500000.0, step=10000.0)
        population_growth = st.number_input("Population Growth (decimal)", value=0.015, step=0.001, format="%.3f")
        gdp_per_capita = st.number_input("GDP per Capita", min_value=0.0, value=18000.0, step=500.0)
        gdp_growth = st.number_input("GDP Growth (decimal)", value=0.02, step=0.001, format="%.3f")

    with col2:
        residential_energy = st.number_input("Residential Energy Activity", min_value=0.0, value=1200000.0)
        transport_activity = st.number_input("Transport Activity", min_value=0.0, value=800000000.0)
        industrial_output = st.number_input("Industrial Activity", min_value=0.0, value=450000.0)
        waste_activity = st.number_input("Waste Activity", min_value=0.0, value=180000.0)
        grid_energy = st.number_input("Grid Energy Activity", min_value=0.0, value=2300000.0)

    activity_df = manual_input_to_activity(
        residential_energy=residential_energy,
        transport_activity=transport_activity,
        industrial_output=industrial_output,
        waste_activity=waste_activity,
        grid_energy=grid_energy,
    )
    meta = {
        "city_name": city_name,
        "population": population,
        "population_growth": population_growth,
        "gdp_per_capita": gdp_per_capita,
        "gdp_growth": gdp_growth,
    }
    return activity_df, meta


def _upload_input_panel() -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    st.info("Upload city activity and optional emission factor data (CSV or Excel)")
    activity_upload = st.file_uploader("City activity file", type=["csv", "xlsx", "xls"], key="activity_upload")
    factor_upload = st.file_uploader("Emission factors file", type=["csv", "xlsx", "xls"], key="factor_upload")

    activity_df = load_activity_data(activity_upload) if activity_upload else None
    factor_df = load_factor_data(factor_upload) if factor_upload else None

    if activity_df is not None:
        st.dataframe(activity_df, use_container_width=True)
    if factor_df is not None:
        st.dataframe(factor_df, use_container_width=True)

    return activity_df, factor_df


def _clear_report_cache() -> None:
    for key in ("excel_report_bytes", "pdf_report_bytes"):
        if key in st.session_state:
            del st.session_state[key]


def main() -> None:
    st.title("CityScale - Urban Emissions Simulator")
    st.caption("Multi-sector urban GHG modeling, scenario forecasting, and reporting.")

    st.sidebar.header("Configuration")
    input_mode = st.sidebar.radio("Input Mode", ["Manual", "Upload"], index=0)
    start_year, end_year = st.sidebar.slider("Forecast horizon", min_value=2025, max_value=2050, value=(2025, 2050))

    st.sidebar.subheader("Mitigation Scenario")
    energy_efficiency = st.sidebar.slider("Energy efficiency (%)", 0, 80, 20) / 100
    renewable_share = st.sidebar.slider("Renewable share (%)", 0, 100, 30) / 100
    modal_shift = st.sidebar.slider("Transport modal shift (%)", 0, 80, 15) / 100
    industry_efficiency = st.sidebar.slider("Industry efficiency (%)", 0, 80, 10) / 100
    waste_reduction = st.sidebar.slider("Waste reduction (%)", 0, 80, 15) / 100

    st.sidebar.subheader("Urban Form")
    density = st.sidebar.number_input("Density (people/km2)", min_value=100.0, value=4000.0, step=100.0)
    compactness = st.sidebar.slider("Compactness index", 0.0, 1.0, 0.5)
    transit_access = st.sidebar.slider("Transit access index", 0.0, 1.0, 0.5)

    factor_df = _load_default_factors()

    if input_mode == "Manual":
        activity_df, meta = _manual_input_panel()
    else:
        uploaded_activity, uploaded_factors = _upload_input_panel()
        activity_df = uploaded_activity
        if uploaded_factors is not None:
            factor_df = uploaded_factors
        meta = {
            "city_name": st.text_input("City Name", "Uploaded City"),
            "population": st.number_input("Population", min_value=0.0, value=1500000.0, step=10000.0),
            "population_growth": st.number_input("Population Growth (decimal)", value=0.015, step=0.001, format="%.3f"),
            "gdp_per_capita": st.number_input("GDP per Capita", min_value=0.0, value=18000.0, step=500.0),
            "gdp_growth": st.number_input("GDP Growth (decimal)", value=0.02, step=0.001, format="%.3f"),
        }

    if st.button("Run Simulation", type="primary"):
        if activity_df is None:
            st.error("Please provide activity data via manual entry or upload.")
            st.stop()

        activity_errors, activity_warnings = validate_activity_data(activity_df)
        factor_errors, factor_warnings = validate_factor_data(factor_df)
        for warn in activity_warnings + factor_warnings:
            st.warning(warn)
        if activity_errors or factor_errors:
            for err in activity_errors + factor_errors:
                st.error(err)
            st.stop()

        base_sector_results = compute_sector_emissions(activity_df, factor_df)
        gdp_total = meta["population"] * meta["gdp_per_capita"]
        base_summary = aggregate_emissions(base_sector_results, population=meta["population"], gdp=gdp_total)

        params = UrbanFormParameters(
            density_per_km2=density,
            compactness_index=compactness,
            transit_access_index=transit_access,
        )
        urban_modifiers = calculate_urban_modifiers(params)

        scenarios = [
            Scenario(name="Baseline"),
            Scenario(
                name="Mitigation",
                energy_efficiency=energy_efficiency,
                renewable_share=renewable_share,
                modal_shift=modal_shift,
                industry_efficiency=industry_efficiency,
                waste_reduction=waste_reduction,
            ),
        ]

        forecast_df = forecast_scenarios(
            base_activity_df=activity_df,
            factor_df=factor_df,
            population_base=meta["population"],
            population_growth=meta["population_growth"],
            gdp_per_capita_base=meta["gdp_per_capita"],
            gdp_growth=meta["gdp_growth"],
            start_year=start_year,
            end_year=end_year,
            scenarios=scenarios,
            urban_modifiers=urban_modifiers,
        )

        st.session_state["simulation_results"] = {
            "meta": meta,
            "activity_df": activity_df,
            "factor_df": factor_df,
            "base_sector_results": base_sector_results,
            "base_summary": base_summary,
            "forecast_df": forecast_df,
            "urban_modifiers": urban_modifiers,
        }
        _clear_report_cache()

        run_payload = {
            "meta": meta,
            "urban_modifiers": urban_modifiers,
            "base_summary": base_summary,
            "base_sector_results": base_sector_results.to_dict(orient="records"),
            "forecast": forecast_df.to_dict(orient="records"),
        }
        saved = save_run(RUN_DIR, run_payload)
        st.success(f"Run stored at: {saved.name}")

    results = st.session_state.get("simulation_results")
    if results:
        result_meta = results["meta"]
        result_activity_df = results["activity_df"]
        result_factor_df = results["factor_df"]
        result_sector_df = results["base_sector_results"]
        result_summary = results["base_summary"]
        result_forecast_df = results["forecast_df"]

        col1, col2, col3 = st.columns(3)
        col1.metric("Total CO2e", f"{result_summary['total_co2e']:,.2f}")
        col2.metric("Per Capita CO2e", f"{result_summary['per_capita_co2e']:.6f}")
        col3.metric("Per GDP CO2e", f"{result_summary['per_gdp_co2e']:.10f}")

        sector_fig = sector_bar_chart(result_sector_df)
        scenario_fig = scenario_line_chart(result_forecast_df)
        per_capita_fig = intensity_line_chart(result_forecast_df, metric="per_capita_co2e")
        per_gdp_fig = intensity_line_chart(result_forecast_df, metric="per_gdp_co2e")
        baseline_fig = baseline_comparison_chart(result_forecast_df)
        export_charts = {
            "sector_emissions": sector_fig,
            "scenario_forecast": scenario_fig,
            "per_capita_intensity": per_capita_fig,
            "per_gdp_intensity": per_gdp_fig,
            "baseline_comparison": baseline_fig,
        }

        st.subheader("Base-Year Sector Emissions")
        st.plotly_chart(sector_fig, use_container_width=True)
        st.dataframe(result_sector_df, use_container_width=True)

        st.subheader("Scenario Forecast")
        st.plotly_chart(scenario_fig, use_container_width=True)
        st.plotly_chart(per_capita_fig, use_container_width=True)
        st.plotly_chart(per_gdp_fig, use_container_width=True)
        st.plotly_chart(baseline_fig, use_container_width=True)
        st.dataframe(result_forecast_df, use_container_width=True)

        st.subheader("Export Reports")
        st.caption("Including charts increases report generation time.")
        include_charts = st.checkbox("Include charts in report exports", value=True, key="include_export_charts")
        charts_payload = export_charts if include_charts else None

        col_excel, col_pdf = st.columns(2)
        with col_excel:
            if st.button("Prepare Excel Report", key="prepare_excel_btn"):
                with st.spinner("Generating Excel report..."):
                    st.session_state["excel_report_bytes"] = export_excel_report(
                        base_activity=result_activity_df,
                        factors=result_factor_df,
                        sector_results=result_sector_df,
                        forecast=result_forecast_df,
                        charts=charts_payload,
                    )
            if "excel_report_bytes" in st.session_state:
                st.download_button(
                    label="Download Excel Report",
                    data=st.session_state["excel_report_bytes"],
                    file_name=f"{result_meta['city_name'].replace(' ', '_').lower()}_cityscale_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel_btn",
                )

        with col_pdf:
            if st.button("Prepare PDF Report", key="prepare_pdf_btn"):
                with st.spinner("Generating PDF report..."):
                    st.session_state["pdf_report_bytes"] = export_pdf_report(
                        city_name=result_meta["city_name"],
                        summary=result_summary,
                        sector_results=result_sector_df,
                        forecast=result_forecast_df,
                        charts=charts_payload,
                    )
            if "pdf_report_bytes" in st.session_state:
                st.download_button(
                    label="Download PDF Report",
                    data=st.session_state["pdf_report_bytes"],
                    file_name=f"{result_meta['city_name'].replace(' ', '_').lower()}_cityscale_report.pdf",
                    mime="application/pdf",
                    key="download_pdf_btn",
                )
    else:
        st.caption("Run a simulation to see results and prepare reports.")

    st.subheader("Historical Runs")
    runs = list_runs(RUN_DIR)
    if runs:
        selected = st.selectbox("Load run", [r.name for r in runs])
        if st.button("Load Selected Run"):
            loaded = load_run(RUN_DIR / selected)
            st.json(loaded)
    else:
        st.caption("No saved runs yet.")


if __name__ == "__main__":
    main()
