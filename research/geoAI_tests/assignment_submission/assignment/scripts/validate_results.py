"""
Phase 6: validation. Checks geometry/CRS integrity on the final scored
layer, and prints a full indicator-to-score breakdown for a sample of
high-, medium-, and low-scoring buildings so the rankings can be checked
against geographic common sense rather than accepted blindly.
"""

import geopandas as gpd
import pandas as pd

from config import GEOPACKAGE_PATH, VALIDATION_DIR

RAW_COLS = [
    "nature_dist_m", "nature_count_1km", "river_dist_m", "major_road_dist_m",
    "fieldwork_drive_time_s_mean", "parking_count_1km", "amenity_count_1km",
    "transport_dist_m", "rewilding_community_dist_m",
]
COMPONENT_COLS = [
    "nature_score", "river_corridor_access_score", "amenity_score",
    "parking_score", "transport_score",
]
SUB_COMPONENT_COLS = ["river_score", "fieldwork_access_score", "rewilding_community_score"]


def geometry_checks(gdf: gpd.GeoDataFrame):
    print("--- Geometry / CRS checks on final layer ---")
    print(f"Feature count: {len(gdf)}")
    print(f"CRS: {gdf.crs}")
    print(f"Geometry types: {gdf.geometry.type.value_counts().to_dict()}")
    print(f"Invalid geometries: {(~gdf.geometry.is_valid).sum()}")
    print(f"Duplicate building_id: {gdf['building_id'].duplicated().sum()}")
    print(f"Missing livability_score: {gdf['livability_score'].isna().sum()}")
    print(f"livability_score range: {gdf['livability_score'].min():.1f} - {gdf['livability_score'].max():.1f}")
    print(f"Rank range: {gdf['livability_rank'].min()} - {gdf['livability_rank'].max()} "
          f"(expect 1 - {len(gdf)})")


def spot_check(gdf: gpd.GeoDataFrame, n_per_tier=3):
    gdf = gdf.sort_values("livability_rank")
    n = len(gdf)
    tiers = {
        "HIGH (top)": gdf.iloc[:n_per_tier],
        "MEDIUM (middle)": gdf.iloc[n // 2 - n_per_tier // 2: n // 2 - n_per_tier // 2 + n_per_tier],
        "LOW (bottom)": gdf.iloc[-n_per_tier:],
    }
    lines = []
    for tier_name, sample in tiers.items():
        lines.append(f"\n=== {tier_name} ===")
        for _, row in sample.iterrows():
            lines.append(
                f"\nbuilding_id={row['building_id']}  rank={row['livability_rank']}  "
                f"livability_score={row['livability_score']:.1f}  "
                f"location=({row.geometry.centroid.y:.5f}, {row.geometry.centroid.x:.5f})  "
                f"addr_city={row.get('addr:city', 'n/a')}"
            )
            lines.append("  raw indicators: " + ", ".join(f"{c}={row[c]:.1f}" for c in RAW_COLS))
            lines.append("  component scores: " + ", ".join(f"{c}={row[c]:.1f}" for c in COMPONENT_COLS))
            lines.append("  river-corridor sub-scores: " + ", ".join(f"{c}={row[c]:.1f}" for c in SUB_COMPONENT_COLS))
    text = "\n".join(lines)
    print(text)
    return text


if __name__ == "__main__":
    gdf = gpd.read_file(GEOPACKAGE_PATH, layer="apartment_buildings")
    geometry_checks(gdf)
    report_text = spot_check(gdf)

    out_path = VALIDATION_DIR / "score_spot_checks.md"
    with open(out_path, "w") as f:
        f.write("# Livability score spot checks\n\n")
        f.write("High, medium, and low scoring apartment buildings, with their full\n")
        f.write("raw-indicator-to-final-score breakdown, for geographic sanity checking.\n")
        f.write(report_text)
    print(f"\nSaved to {out_path}")
