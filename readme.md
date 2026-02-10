# CityScale: Urban Emissions Simulator

CityScale is a Streamlit app for city-level greenhouse gas analysis across five sectors:
- residential buildings
- transport
- industry
- waste
- energy

The app supports baseline and mitigation forecasting, urban-form sensitivity, visual dashboards, downloadable reports, and run history persistence.

## What the app does

- Accepts city activity input from manual forms or CSV/Excel upload
- Calculates sector emissions using activity-factor multiplication
- Converts CH4 and N2O to CO2e using default GWP factors
- Computes total, per-capita, and per-GDP emissions
- Compares a mitigation scenario against a baseline scenario
- Forecasts annually for a selected range from 2025 to 2050
- Applies urban form modifiers (density, compactness, transit access)
- Exports results to Excel and PDF
- Stores simulation runs as JSON for later inspection

## Technology stack

- Python
- Streamlit
- pandas
- Plotly
- ReportLab
- pytest

## Project layout

```text
cityscale/
├── app.py
├── requirements.txt
├── readme.md
├── data/
│   ├── emission_factors.csv
│   ├── sample_city_data.xlsx
│   ├── sample_datasets/
│   │   └── sample_city_data.csv
│   └── templates/
│       └── city_activity_template.csv
├── modules/
│   ├── drivers.py
│   ├── emissions_engine.py
│   ├── io_handlers.py
│   ├── report_export.py
│   ├── scenario.py
│   ├── storage.py
│   ├── urban_form.py
│   ├── utils.py
│   └── visualization.py
└── tests/
    ├── test_emissions_engine.py
    ├── test_io.py
    ├── test_scenario.py
    ├── test_storage.py
    └── test_urban_form.py
```

## Quick start

### 1) Install dependencies

```bash
cd "personal project/cityscaleapps/cityscale"
python3 -m pip install -r requirements.txt
```

### 2) Run the app

```bash
streamlit run app.py
```

### 3) Run tests

```bash
python3 -m pytest -q
```

## Input data specification

### Activity data (required)

Required columns:
- `sector`
- `activity`

Expected sector names:
- `residential`
- `transport`
- `industry`
- `waste`
- `energy`

Rules enforced by validation:
- no missing `sector` values
- no missing `activity` values
- no negative activity values
- zero activity values are allowed, but shown as warnings

### Emission factor data (optional upload, defaults provided)

Required columns:
- `sector`
- `co2_factor`
- `ch4_factor`
- `n2o_factor`

Rules enforced by validation:
- no missing required columns
- no null factor values
- no negative factor values
- duplicate sectors trigger a warning

Default factors file:
- `data/emission_factors.csv`

Templates and sample inputs:
- `data/templates/city_activity_template.csv`
- `data/sample_datasets/sample_city_data.csv`
- `data/sample_city_data.xlsx`

## Manual input fields in UI

### City and macro inputs

- City name
- Population
- Population growth (decimal, e.g. `0.015`)
- GDP per capita
- GDP growth (decimal, e.g. `0.020`)

### Sector activity inputs

- Residential energy activity
- Transport activity
- Industrial activity
- Waste activity
- Grid energy activity

### Scenario controls

- Energy efficiency (%)
- Renewable share (%)
- Transport modal shift (%)
- Industry efficiency (%)
- Waste reduction (%)

### Urban form controls

- Density (people per km2)
- Compactness index (0-1)
- Transit access index (0-1)

### Forecast horizon

- Year range slider from 2025 to 2050

## Modeling approach

### Core emissions equation

For each sector:

`CO2 = activity * co2_factor`  
`CH4 = activity * ch4_factor`  
`N2O = activity * n2o_factor`  
`CO2e = CO2 + CH4*28 + N2O*265`

Default GWP values:
- CO2: `1`
- CH4: `28`
- N2O: `265`

### Aggregates

- `total_co2e = sum(sector co2e)`
- `per_capita_co2e = total_co2e / population`
- `per_gdp_co2e = total_co2e / gdp`

### Scenario transformations

Mitigation scenario modifies activity and factors:
- Residential and energy activity reduced by `energy_efficiency`
- Transport activity reduced by `modal_shift`
- Industry activity reduced by `industry_efficiency`
- Waste activity reduced by `waste_reduction`
- Energy sector emission factors reduced by `renewable_share`

All scenario percentages are clamped to `[0, 1]`.

### Forecast scaling

For year `t` relative to forecast start:
- `population_t = population_0 * (1 + population_growth)^t`
- `gdp_per_capita_t = gdp_per_capita_0 * (1 + gdp_growth)^t`

Activity growth assumptions:
- Residential, transport, waste scale with population
- Industry and energy scale with average of population and GDP growth factors

### Urban form modifiers

Urban form computes multiplicative modifiers and applies them before scenario adjustments:
- transport modifier (density, compactness, transit access)
- residential modifier (compactness)
- energy modifier (compactness)

## Outputs in the app

### Dashboard metrics

- Total CO2e
- Per-capita CO2e
- Per-GDP CO2e

### Charts

- Sector emissions bar chart
- Scenario forecast line chart
- Per-capita intensity line chart
- Per-GDP intensity line chart
- Percent change vs baseline bar chart

### Tables

- Base-year sector emissions table
- Scenario forecast table

## Exported reports

### Excel report

Downloaded workbook includes sheets:
- `BaseActivity`
- `EmissionFactors`
- `BaseResults`
- `ScenarioForecast`
- `Charts` (embedded chart images generated from the app figures)

Generation flow:
- click `Prepare Excel Report`
- then click `Download Excel Report`

### PDF report

Includes:
- city and summary metrics
- sector emission list
- latest-year scenario highlights vs baseline
- chart pages with the same main figures shown in the app

Generation flow:
- click `Prepare PDF Report`
- then click `Download PDF Report`

## Historical run storage

Every simulation run is saved to:
- `runs/run_<timestamp>.json`

Saved payload includes:
- input metadata
- urban modifiers
- base summary
- base sector results
- forecast records

The UI can list and display saved runs from the same folder.

## Module guide

- `modules/drivers.py`: data models for population, GDP, sector activity, synthetic sample generation
- `modules/emissions_engine.py`: sector calculations and aggregate metrics
- `modules/scenario.py`: scenario adjustment logic and forecast generation
- `modules/urban_form.py`: urban-form modifier calculations and optional GeoJSON bounds helper
- `modules/io_handlers.py`: CSV/Excel loading and validation functions
- `modules/visualization.py`: Plotly chart builders
- `modules/report_export.py`: Excel and PDF export functions
- `modules/storage.py`: run save/list/load helpers
- `modules/utils.py`: utility helpers and constants

## Testing

Current test coverage includes:
- emission calculation correctness
- scenario transformation and baseline comparison behavior
- urban-form modifier bounds and application
- I/O validation behavior
- run storage round-trip

Run:

```bash
python3 -m pytest -q
```

## Troubleshooting

- `ModuleNotFoundError` when running app:
  install dependencies with `python3 -m pip install -r requirements.txt`
- Upload errors:
  confirm required columns exactly match schema above
- Empty or unexpected results:
  check sector names match expected values (`residential`, `transport`, `industry`, `waste`, `energy`)
- Streamlit command not found:
  use `python3 -m streamlit run app.py`
- Charts missing in exported reports:
  ensure `kaleido` is installed (`python3 -m pip install kaleido`)

## Notes and extension ideas

- `modules/urban_form.py` includes `load_geojson_bounds()` for future spatial integration.
- Scenario architecture supports adding more named scenarios if needed.
- You can plug in custom GWP values through the emissions engine API in code if policy assumptions change.
