"""
Phase 3 (step 1): acquire municipal boundaries for the candidate study area
and check apartment-building counts per municipality, so the final study-area
definition is based on evidence rather than assumption.
"""

import geopandas as gpd
import osmnx as ox

from config import (
    CANDIDATE_MUNICIPALITIES,
    DATA_RAW,
    GEOGRAPHIC_CRS,
    APARTMENT_TAGS,
)


def fetch_municipal_boundaries() -> gpd.GeoDataFrame:
    """Fetch each candidate municipality's boundary polygon from OSM."""
    frames = []
    for place in CANDIDATE_MUNICIPALITIES:
        gdf = ox.geocode_to_gdf(place)
        gdf["municipality"] = place.split(",")[0]
        frames.append(gdf)
    boundaries = gpd.GeoDataFrame(
        gpd.pd.concat(frames, ignore_index=True), crs=frames[0].crs
    ).to_crs(GEOGRAPHIC_CRS)
    return boundaries


def count_apartments_per_municipality(boundaries: gpd.GeoDataFrame) -> gpd.pd.DataFrame:
    """Count building=apartments features within each municipal polygon."""
    counts = []
    for _, row in boundaries.iterrows():
        name = row["municipality"]
        try:
            buildings = ox.features_from_polygon(row.geometry, tags=APARTMENT_TAGS)
            n = len(buildings)
        except ox._errors.InsufficientResponseError:
            n = 0
        counts.append({"municipality": name, "apartment_building_count": n})
    return gpd.pd.DataFrame(counts)


if __name__ == "__main__":
    print("Fetching municipal boundaries from OSM...")
    boundaries = fetch_municipal_boundaries()
    print(f"Fetched {len(boundaries)} municipal boundaries.")
    print(boundaries[["municipality", "geometry"]].head())
    print("CRS:", boundaries.crs)
    print("Bounds:", boundaries.total_bounds)

    out_path = DATA_RAW / "candidate_municipalities.gpkg"
    boundaries.to_file(out_path, layer="municipalities", driver="GPKG")
    print(f"Saved to {out_path}")

    print("\nCounting building=apartments per municipality (evidence check)...")
    counts = count_apartments_per_municipality(boundaries)
    print(counts.to_string(index=False))
    counts.to_csv(DATA_RAW / "apartment_counts_per_municipality.csv", index=False)
