import pandas as pd

from modules.urban_form import UrbanFormParameters, apply_urban_form_modifiers, calculate_urban_modifiers


def test_urban_modifiers_stay_in_reasonable_range():
    params = UrbanFormParameters(density_per_km2=8000, compactness_index=0.7, transit_access_index=0.8)
    modifiers = calculate_urban_modifiers(params)

    assert 0.45 <= modifiers["transport"] <= 1.1
    assert 0.8 <= modifiers["residential"] <= 1.05


def test_apply_urban_modifiers_changes_activity():
    df = pd.DataFrame({"sector": ["transport", "residential"], "activity": [100.0, 200.0]})
    out = apply_urban_form_modifiers(df, {"transport": 0.8, "residential": 0.9})

    assert float(out[out["sector"] == "transport"]["activity"].iloc[0]) == 80.0
    assert float(out[out["sector"] == "residential"]["activity"].iloc[0]) == 180.0
