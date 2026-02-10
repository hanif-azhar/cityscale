from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd

REQUIRED_ACTIVITY_COLUMNS = ["sector", "activity"]
REQUIRED_FACTOR_COLUMNS = ["sector", "co2_factor", "ch4_factor", "n2o_factor"]


def _read_file(file_obj) -> pd.DataFrame:
    name = getattr(file_obj, "name", "")
    if name.endswith(".csv"):
        return pd.read_csv(file_obj)
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(file_obj)
    raise ValueError("Unsupported file format. Use CSV or Excel.")


def load_activity_data(file_obj: BinaryIO | str | Path) -> pd.DataFrame:
    if isinstance(file_obj, (str, Path)):
        path = Path(file_obj)
        if path.suffix.lower() == ".csv":
            return pd.read_csv(path)
        if path.suffix.lower() in {".xlsx", ".xls"}:
            return pd.read_excel(path)
        raise ValueError("Unsupported activity file extension")
    return _read_file(file_obj)


def load_factor_data(file_obj: BinaryIO | str | Path) -> pd.DataFrame:
    return load_activity_data(file_obj)


def validate_activity_data(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    missing = [c for c in REQUIRED_ACTIVITY_COLUMNS if c not in df.columns]
    if missing:
        errors.append(f"Missing columns: {missing}")
        return errors, warnings

    if df["sector"].isna().any():
        errors.append("Sector values cannot be empty")

    if df["activity"].isna().any():
        errors.append("Activity values cannot be empty")

    if (df["activity"] < 0).any():
        errors.append("Activity values must be non-negative")

    if (df["activity"] == 0).any():
        warnings.append("Some activities are zero; this may understate emissions")

    return errors, warnings


def validate_factor_data(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    missing = [c for c in REQUIRED_FACTOR_COLUMNS if c not in df.columns]
    if missing:
        errors.append(f"Missing columns: {missing}")
        return errors, warnings

    for col in ["co2_factor", "ch4_factor", "n2o_factor"]:
        if df[col].isna().any():
            errors.append(f"Column has null values: {col}")
        if (df[col] < 0).any():
            errors.append(f"Column has negative factors: {col}")

    if df["sector"].duplicated().any():
        warnings.append("Duplicate sectors in factor table; first match will be used")

    return errors, warnings


def manual_input_to_activity(
    residential_energy: float,
    transport_activity: float,
    industrial_output: float,
    waste_activity: float,
    grid_energy: float,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sector": ["residential", "transport", "industry", "waste", "energy"],
            "activity": [residential_energy, transport_activity, industrial_output, waste_activity, grid_energy],
        }
    )
