"""
Phase 3 (step 2): build the final study-area polygon and extract, clean, and
validate the apartment-building layer within it.
"""

import geopandas as gpd
import osmnx as ox

from config import (
    DATA_RAW,
    DATA_PROCESSED,
    STUDY_AREA_MUNICIPALITIES,
    GEOGRAPHIC_CRS,
    METRIC_CRS,
    APARTMENT_TAGS,
)


def build_study_area() -> gpd.GeoDataFrame:
    """Dissolve the final set of municipal boundaries into one study-area polygon."""
    all_municipalities = gpd.read_file(DATA_RAW / "candidate_municipalities.gpkg", layer="municipalities")
    keep_names = [m.split(",")[0] for m in STUDY_AREA_MUNICIPALITIES]
    subset = all_municipalities[all_municipalities["municipality"].isin(keep_names)].copy()
    dissolved = subset.dissolve()
    dissolved = gpd.GeoDataFrame(
        {"name": ["Coa Valley study area (Guarda + Pinhel + Vila Nova de Foz Coa)"]},
        geometry=[dissolved.geometry.iloc[0]],
        crs=subset.crs,
    )
    return dissolved


def fetch_apartment_buildings(study_area: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Pull building=apartments from OSM within the study-area polygon and clean it."""
    polygon = study_area.geometry.iloc[0]
    raw = ox.features_from_polygon(polygon, tags=APARTMENT_TAGS)

    # Keep only polygon/multipolygon geometries (drop stray nodes/lines tagged
    # the same way, which do not represent a building footprint).
    raw = raw[raw.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()

    # Drop invalid geometries, repairing where a simple buffer(0) fixes them.
    invalid_before = (~raw.geometry.is_valid).sum()
    raw["geometry"] = raw.geometry.buffer(0)
    invalid_after = (~raw.geometry.is_valid).sum()

    # Drop exact geometry duplicates (can occur when a building is tagged
    # on both an outer way and a multipolygon relation).
    raw = raw.reset_index()
    n_before_dedup = len(raw)
    raw["wkb"] = raw.geometry.apply(lambda g: g.wkb)
    raw = raw.drop_duplicates(subset="wkb").drop(columns="wkb")
    n_after_dedup = len(raw)

    raw["building_id"] = range(1, len(raw) + 1)

    keep_cols = ["building_id", "osmid", "element", "name", "building", "building:levels",
                 "addr:city", "addr:street", "addr:housenumber", "geometry"]
    keep_cols = [c for c in keep_cols if c in raw.columns]
    buildings = gpd.GeoDataFrame(raw[keep_cols], geometry="geometry", crs=raw.crs).to_crs(GEOGRAPHIC_CRS)

    print(f"Invalid geometries: {invalid_before} before repair, {invalid_after} after buffer(0)")
    print(f"Duplicate geometries dropped: {n_before_dedup - n_after_dedup}")
    return buildings


if __name__ == "__main__":
    print("Building final study-area polygon...")
    study_area = build_study_area()
    print("Study area CRS:", study_area.crs)
    print("Study area bounds:", study_area.total_bounds)
    print("Study area sq km:", study_area.to_crs(METRIC_CRS).geometry.area.iloc[0] / 1e6)
    study_area.to_file(DATA_PROCESSED / "study_area.gpkg", layer="study_area", driver="GPKG")

    print("\nFetching apartment buildings from OSM...")
    buildings = fetch_apartment_buildings(study_area)

    print(f"\nFeature count: {len(buildings)}")
    print("CRS:", buildings.crs)
    print("Geometry types:", buildings.geometry.type.value_counts().to_dict())
    print("Bounds:", buildings.total_bounds)
    print("\nSample attributes:")
    print(buildings.drop(columns="geometry").head(10).to_string())
    print("\nNon-null attribute counts:")
    print(buildings.drop(columns="geometry").notna().sum())

    buildings.to_file(DATA_PROCESSED / "apartment_buildings_raw.gpkg", layer="apartment_buildings", driver="GPKG")
    print(f"\nSaved to {DATA_PROCESSED / 'apartment_buildings_raw.gpkg'}")
