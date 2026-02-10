from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

DEFAULT_GWP = {"CO2": 1.0, "CH4": 28.0, "N2O": 265.0}


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def year_range(start_year: int, end_year: int) -> List[int]:
    if end_year < start_year:
        raise ValueError("end_year must be >= start_year")
    return list(range(start_year, end_year + 1))


def now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_positive_fields(values: dict, fields: Iterable[str]) -> list[str]:
    errors: list[str] = []
    for field in fields:
        val = values.get(field)
        if val is None:
            errors.append(f"Missing value: {field}")
        elif float(val) < 0:
            errors.append(f"Negative value is not allowed: {field}")
    return errors
