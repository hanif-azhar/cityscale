from __future__ import annotations

import json
from dataclasses import dataclass
from math import log1p
from pathlib import Path
from typing import Dict

import pandas as pd

from .utils import clamp


@dataclass
class UrbanFormParameters:
    density_per_km2: float = 4000.0
    compactness_index: float = 0.5
    transit_access_index: float = 0.5


def calculate_urban_modifiers(params: UrbanFormParameters) -> Dict[str, float]:
    density_effect = clamp(1.0 - 0.08 * log1p(max(params.density_per_km2, 1.0) / 1000.0), 0.65, 1.05)
    compactness_effect = clamp(1.0 - 0.2 * params.compactness_index, 0.75, 1.05)
    transit_effect = clamp(1.0 - 0.25 * params.transit_access_index, 0.7, 1.05)

    transport_modifier = clamp(density_effect * compactness_effect * transit_effect, 0.45, 1.1)
    building_modifier = clamp(1.0 - 0.1 * params.compactness_index, 0.8, 1.05)

    return {
        "transport": transport_modifier,
        "residential": building_modifier,
        "energy": building_modifier,
    }


def apply_urban_form_modifiers(activity_df: pd.DataFrame, modifiers: Dict[str, float]) -> pd.DataFrame:
    df = activity_df.copy()
    for sector, modifier in modifiers.items():
        mask = df["sector"] == sector
        if mask.any():
            df.loc[mask, "activity"] = df.loc[mask, "activity"] * modifier
    return df


def load_geojson_bounds(path: str | Path) -> dict | None:
    geo_path = Path(path)
    if not geo_path.exists():
        return None

    data = json.loads(geo_path.read_text())
    coords = []
    for feature in data.get("features", []):
        geom = feature.get("geometry", {})
        if geom.get("type") == "Polygon":
            for ring in geom.get("coordinates", []):
                coords.extend(ring)

    if not coords:
        return None

    xs = [pt[0] for pt in coords]
    ys = [pt[1] for pt in coords]
    return {"min_x": min(xs), "max_x": max(xs), "min_y": min(ys), "max_y": max(ys)}
