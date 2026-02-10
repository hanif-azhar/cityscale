import pandas as pd

from modules.io_handlers import validate_activity_data, validate_factor_data


def test_validate_activity_data_flags_negative():
    df = pd.DataFrame({"sector": ["transport"], "activity": [-1.0]})
    errors, warnings = validate_activity_data(df)

    assert errors
    assert not warnings


def test_validate_factor_data_detects_missing_columns():
    df = pd.DataFrame({"sector": ["transport"], "co2_factor": [1.0]})
    errors, _ = validate_factor_data(df)

    assert errors
