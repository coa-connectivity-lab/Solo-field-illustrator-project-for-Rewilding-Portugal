"""
Phase 4: compute raw livability indicators for each apartment building, one
category at a time, printing distributions for validation after each.

All distance work happens in the metric CRS (EPSG:3763) so results are in
metres, not degrees. Building geometry -> a representative point uses
centroid in the metric CRS (never on geographic coordinates, which would
distort the result for anything larger than a tiny footprint).
"""

import geopandas as gpd
import numpy as np
import pandas as pd

from config import (
    DATA_PROCESSED,
    METRIC_CRS,
    GEOGRAPHIC_CRS,
    COUNT_RADIUS_M,
    FIELDWORK_DESTINATIONS,
    REWILDING_COMMUNITY_POINTS,
)

OUT_PATH = DATA_PROCESSED / "apartment_buildings_with_indicators.gpkg"


def load_buildings():
    buildings = gpd.read_file(DATA_PROCESSED / "apartment_buildings_raw.gpkg", layer="apartment_buildings")
    buildings = buildings.to_crs(METRIC_CRS)
    buildings["centroid"] = buildings.geometry.centroid
    return buildings


def load_layer(name):
    path = DATA_PROCESSED / f"{name}.gpkg"
    gdf = gpd.read_file(path, layer=name).to_crs(METRIC_CRS)
    return gdf


def nearest_distance(points: gpd.GeoSeries, targets: gpd.GeoDataFrame) -> np.ndarray:
    """Distance in metres from each point to the nearest geometry in targets."""
    points_gdf = gpd.GeoDataFrame(geometry=points, crs=points.crs)
    joined = gpd.sjoin_nearest(points_gdf, targets[["geometry"]], distance_col="dist_m")
    # sjoin_nearest can return >1 row per point on exact ties; keep the closest.
    joined = joined.groupby(joined.index)["dist_m"].min()
    return joined.reindex(range(len(points))).to_numpy()


def count_within_radius(points: gpd.GeoSeries, targets: gpd.GeoDataFrame, radius_m: float) -> np.ndarray:
    buffers = gpd.GeoDataFrame(geometry=points.buffer(radius_m), crs=points.crs)
    joined = gpd.sjoin(buffers, targets[["geometry"]], predicate="intersects", how="left")
    counts = joined.groupby(joined.index).size()
    # sjoin drops rows with no match entirely in some geopandas versions' left join
    # only when there is truly no other column; guard by reindexing to full range.
    return counts.reindex(range(len(points)), fill_value=0).to_numpy()


def validate(name: str, series: pd.Series):
    print(f"\n--- {name} ---")
    print(f"count={series.count()}, missing={series.isna().sum()}")
    print(series.describe().to_string())


if __name__ == "__main__":
    buildings = load_buildings()
    centroids = gpd.GeoSeries(buildings["centroid"], crs=METRIC_CRS)
    n = len(buildings)
    print(f"Computing indicators for {n} apartment buildings...")

    # --- A. Nature and recreation --------------------------------------
    nature = load_layer("nature_areas")
    buildings["nature_dist_m"] = nearest_distance(centroids, nature)
    buildings["nature_count_1km"] = count_within_radius(centroids, nature, COUNT_RADIUS_M["park"])
    validate("nature_dist_m", buildings["nature_dist_m"])
    validate("nature_count_1km", buildings["nature_count_1km"])

    # --- B. Coa river / natural environment -----------------------------
    river = load_layer("coa_river")
    buildings["river_dist_m"] = nearest_distance(centroids, river)
    validate("river_dist_m", buildings["river_dist_m"])

    # --- C. Field-trip / driving accessibility --------------------------
    major_roads = load_layer("major_roads")
    buildings["major_road_dist_m"] = nearest_distance(centroids, major_roads)
    validate("major_road_dist_m", buildings["major_road_dist_m"])

    ors = pd.read_csv(DATA_PROCESSED / "ors_driving_distances.csv")
    # Select fieldwork drive-time columns explicitly by the destination names
    # configured in FIELDWORK_DESTINATIONS, not by pattern-matching every
    # drive_time_s__* column in the CSV -- the CSV may contain other
    # destinations (e.g. the rewilding-community anchor) that must NOT be
    # folded into this average, or fieldwork_access_score and
    # rewilding_community_score end up built from the same point again.
    fieldwork_names = [d["name"] for d in FIELDWORK_DESTINATIONS]
    drive_time_cols = [f"drive_time_s__{name}" for name in fieldwork_names]
    missing = [c for c in drive_time_cols if c not in ors.columns]
    if missing:
        raise ValueError(f"Expected fieldwork drive-time columns not found in ORS output: {missing}")
    ors["fieldwork_drive_time_s_mean"] = ors[drive_time_cols].mean(axis=1)
    buildings = buildings.merge(ors, on="building_id", how="left")
    validate("fieldwork_drive_time_s_mean", buildings["fieldwork_drive_time_s_mean"])

    # --- D. Parking (Mapped Parking Access) -----------------------------
    parking = load_layer("parking")
    buildings["parking_count_1km"] = count_within_radius(centroids, parking, COUNT_RADIUS_M["parking"])
    validate("parking_count_1km", buildings["parking_count_1km"])

    # --- E. Everyday amenities -------------------------------------------
    amenities = load_layer("amenities")
    buildings["amenity_count_1km"] = count_within_radius(centroids, amenities, COUNT_RADIUS_M["amenity"])
    validate("amenity_count_1km", buildings["amenity_count_1km"])

    # --- F. Public transport ---------------------------------------------
    transport = load_layer("transport_stops")
    buildings["transport_dist_m"] = nearest_distance(centroids, transport)
    validate("transport_dist_m", buildings["transport_dist_m"])

    # --- G. Scientific / rewilding community -----------------------------
    # Real ORS driving distance to Vale Carapito (Rewilding Portugal reserve),
    # already computed in acquire_ors_driving_distances.py -- reuse it rather
    # than recomputing a straight-line distance to the same point.
    rewilding_names = [d["name"] for d in REWILDING_COMMUNITY_POINTS]
    rewilding_cols = [f"drive_dist_m__{name}" for name in rewilding_names]
    missing = [c for c in rewilding_cols if c not in buildings.columns]
    if missing:
        raise ValueError(f"Expected rewilding-community distance columns not found: {missing}")
    buildings["rewilding_community_dist_m"] = buildings[rewilding_cols].min(axis=1)
    validate("rewilding_community_dist_m", buildings["rewilding_community_dist_m"])

    # --- Save raw indicators for the scoring step ------------------------
    buildings = buildings.drop(columns=["centroid"])
    buildings_out = buildings.to_crs(GEOGRAPHIC_CRS)
    buildings_out.to_file(OUT_PATH, layer="apartment_buildings", driver="GPKG")
    print(f"\nSaved {len(buildings_out)} buildings with raw indicators to {OUT_PATH}")
    print("Columns:", list(buildings_out.columns))
