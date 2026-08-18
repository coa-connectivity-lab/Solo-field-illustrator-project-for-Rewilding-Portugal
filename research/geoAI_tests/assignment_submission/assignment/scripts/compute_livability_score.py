"""
Phase 5: normalize raw indicators, combine into component scores, apply
weights to get the final 0-100 livability_score and rank, and compute the
three sensitivity-analysis scenarios (nature_emphasis, balanced,
practical_residential) as additional columns rather than overwriting the
primary score.
"""

import geopandas as gpd
import numpy as np
import pandas as pd

from config import (
    DATA_PROCESSED,
    OUTPUT_DIR,
    OUTPUT_TABLES,
    GEOPACKAGE_PATH,
    DISTANCE_CUTOFFS_M,
    FIELDWORK_DRIVE_TIME_CUTOFF_S,
    COUNT_CAP_PERCENTILE,
    NATURE_SUBWEIGHTS,
    FIELDWORK_ACCESS_SUBWEIGHTS,
    RIVER_CORRIDOR_SUBWEIGHTS,
    LIVABILITY_WEIGHTS,
    SCENARIO_WEIGHTS,
)

IN_PATH = DATA_PROCESSED / "apartment_buildings_with_indicators.gpkg"


def distance_score(dist_m: pd.Series, cutoff_m: float) -> pd.Series:
    """Shorter distance = higher score. 100 at 0m, 0 at or beyond cutoff, linear between."""
    score = 100 * (1 - dist_m / cutoff_m)
    return score.clip(lower=0, upper=100)


def count_score(count: pd.Series, cap_percentile: float) -> pd.Series:
    """More features = higher score, capped at a percentile so one outlier
    location cannot stretch the scale for everyone else, then min-max scaled
    across the (capped) sample so the achievable range is used fully."""
    cap = np.percentile(count, cap_percentile)
    capped = count.clip(upper=cap)
    lo, hi = capped.min(), capped.max()
    if hi == lo:
        return pd.Series(100.0, index=count.index)
    return 100 * (capped - lo) / (hi - lo)


def weighted_score(components: pd.DataFrame, weights: dict) -> pd.Series:
    total_weight = sum(weights.values())
    score = sum(components[k] * w for k, w in weights.items()) / total_weight
    return score


if __name__ == "__main__":
    buildings = gpd.read_file(IN_PATH, layer="apartment_buildings")
    n = len(buildings)
    print(f"Scoring {n} apartment buildings...")

    # --- Normalize each raw indicator to a 0-100 sub-score ---------------
    buildings["nature_dist_score"] = distance_score(buildings["nature_dist_m"], DISTANCE_CUTOFFS_M["nature"])
    buildings["nature_count_score"] = count_score(buildings["nature_count_1km"], COUNT_CAP_PERCENTILE)
    buildings["nature_score"] = (
        NATURE_SUBWEIGHTS["dist"] * buildings["nature_dist_score"]
        + NATURE_SUBWEIGHTS["count"] * buildings["nature_count_score"]
    )

    buildings["river_score"] = distance_score(buildings["river_dist_m"], DISTANCE_CUTOFFS_M["river"])

    buildings["fieldwork_drive_time_score"] = distance_score(
        buildings["fieldwork_drive_time_s_mean"], FIELDWORK_DRIVE_TIME_CUTOFF_S
    )
    buildings["major_road_score"] = distance_score(buildings["major_road_dist_m"], DISTANCE_CUTOFFS_M["major_road"])
    buildings["fieldwork_access_score"] = (
        FIELDWORK_ACCESS_SUBWEIGHTS["drive_time"] * buildings["fieldwork_drive_time_score"]
        + FIELDWORK_ACCESS_SUBWEIGHTS["major_road"] * buildings["major_road_score"]
    )

    buildings["parking_score"] = count_score(buildings["parking_count_1km"], COUNT_CAP_PERCENTILE)
    buildings["amenity_score"] = count_score(buildings["amenity_count_1km"], COUNT_CAP_PERCENTILE)
    buildings["transport_score"] = distance_score(buildings["transport_dist_m"], DISTANCE_CUTOFFS_M["public_transport"])
    buildings["rewilding_community_score"] = distance_score(
        buildings["rewilding_community_dist_m"], DISTANCE_CUTOFFS_M["rewilding_community"]
    )

    # river_score, fieldwork_access_score, and rewilding_community_score are
    # kept as individually visible fields (transparency: every raw and
    # normalized indicator stays in the output), but they are combined here
    # into one weighted component before scoring -- see RIVER_CORRIDOR_SUBWEIGHTS
    # in config.py for why: they were found to be measuring largely the same
    # underlying "distance to the Coa valley corridor" signal.
    buildings["river_corridor_access_score"] = (
        RIVER_CORRIDOR_SUBWEIGHTS["river"] * buildings["river_score"]
        + RIVER_CORRIDOR_SUBWEIGHTS["fieldwork_access"] * buildings["fieldwork_access_score"]
        + RIVER_CORRIDOR_SUBWEIGHTS["rewilding_community"] * buildings["rewilding_community_score"]
    )

    component_cols = [
        "nature_score", "river_corridor_access_score", "amenity_score",
        "parking_score", "transport_score",
    ]
    print("\n--- Component score distributions (0-100) ---")
    print(buildings[component_cols].describe().to_string())

    # --- Redundancy check: correlation among component scores ------------
    corr = buildings[component_cols].corr()
    print("\n--- Component score correlation matrix ---")
    print(corr.round(2).to_string())
    high_corr = [
        (a, b, corr.loc[a, b])
        for i, a in enumerate(component_cols)
        for b in component_cols[i + 1:]
        if abs(corr.loc[a, b]) >= 0.7
    ]
    if high_corr:
        print("\nWARNING: highly correlated component pairs (|r| >= 0.7):")
        for a, b, r in high_corr:
            print(f"  {a} <-> {b}: r={r:.2f}")
    else:
        print("\nNo component pair exceeds |r| = 0.7 -- no evidence of double counting.")

    # --- Primary livability score -----------------------------------------
    buildings["livability_score"] = weighted_score(buildings, LIVABILITY_WEIGHTS)
    buildings["livability_rank"] = buildings["livability_score"].rank(ascending=False, method="min").astype(int)

    # --- Sensitivity-analysis scenarios -------------------------------------
    for scenario_name, weights in SCENARIO_WEIGHTS.items():
        buildings[f"livability_score__{scenario_name}"] = weighted_score(buildings, weights)

    print("\n--- Final livability_score distribution ---")
    print(buildings["livability_score"].describe().to_string())

    print("\n--- Top 5 buildings ---")
    print(buildings.nsmallest(5, "livability_rank")[["building_id", "livability_score", "livability_rank"]].to_string(index=False))
    print("\n--- Bottom 5 buildings ---")
    print(buildings.nlargest(5, "livability_rank")[["building_id", "livability_score", "livability_rank"]].to_string(index=False))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    buildings.to_file(GEOPACKAGE_PATH, layer="apartment_buildings", driver="GPKG")
    print(f"\nSaved scored layer to {GEOPACKAGE_PATH}")

    table_path = OUTPUT_TABLES / "livability_scores.csv"
    buildings.drop(columns="geometry").to_csv(table_path, index=False)
    print(f"Saved attribute table to {table_path}")
