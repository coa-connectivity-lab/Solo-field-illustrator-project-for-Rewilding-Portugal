"""
build_tradeoff_maps.py
─────────────────────────
Roads and waterways as dual-purpose infrastructure: the same features drive
both a barrier-to-reintroduction reading and an access-for-eco-tourism
reading (see plan, "Roads & waterways as dual-purpose infrastructure").

Road trade-off:
  barrier_severity  <- 1 / (1 + distance_to_road_m / 1000)   (closer = more barrier)
  access_value      <- same proximity kernel around visitor/interpretive sites
                        (Fóios biodiversity trail, Penascosa, praia fluviais, ...),
                        not around roads themselves - the two layers get compared,
                        not conflated.

Waterway trade-off:
  barrier_severity  <- the Water group's resistance surface (already reflects
                        reduced permeability near infrastructure/impervious
                        surfaces; a simplification - see notebook methodology
                        note - since no separate dam/weir point layer was
                        built for this pass)
  access_value      <- proximity kernel around the same visitor sites, most of
                        which are river beaches (praia fluviais)

Both are classified into conservation_priority / compatible_access / conflict
using each layer's own median split, and written as a single 3-band-style
GeoPackage-friendly output (one raster per surface, per infrastructure type).
"""

import geopandas as gpd
import numpy as np
import rioxarray
from scipy.ndimage import distance_transform_edt

import config

COVARIATE_DIR = config.DATA_PROCESSED / "covariates"
RESISTANCE_DIR = config.DATA_PROCESSED / "resistance"
OUT_DIR = config.OUTPUT_RASTERS

# Known visitor / interpretive sites (from field-trips/*.md and survey123/),
# used as the eco-tourism access-value anchor points.
VISITOR_SITES_WGS84 = [
    ("Pontao Manuel Jose weir", 40.6787318, -6.9239575),
    ("Nascente do Rio Coa / Estacao de Biodiversidade, Foios", 40.2867, -6.8890),
    ("Penascosa rock art reception", 41.0255, -7.0665),
    ("Praia Fluvial de Vale das Eguas", 40.4359044, -7.0243007),
    ("Praia Fluvial de Rapoula do Coa", 40.4183522, -7.054603),
    ("Lageosa (Sorraia horses)", 40.3384, -6.8162),
]


def access_value_kernel(template, decay_km: float = 5.0) -> np.ndarray:
    sites = gpd.GeoDataFrame(
        {"name": [s[0] for s in VISITOR_SITES_WGS84]},
        geometry=gpd.points_from_xy([s[2] for s in VISITOR_SITES_WGS84], [s[1] for s in VISITOR_SITES_WGS84]),
        crs=config.CRS_DISPLAY,
    ).to_crs(config.CRS_METRIC)

    # Also include this project's own visited Survey123 sites
    visited = gpd.read_file(config.DATA_PROCESSED / "field_observations.gpkg", layer="visited_sites")
    all_sites = pd_concat_points(sites, visited)

    transform = template.rio.transform()
    rows, cols = template.shape
    site_mask = np.ones((rows, cols), dtype=bool)
    for geom in all_sites.geometry:
        col, row = ~transform * (geom.x, geom.y)
        row, col = int(row), int(col)
        if 0 <= row < rows and 0 <= col < cols:
            site_mask[row, col] = False

    px_size = abs(transform.a)
    dist_px = distance_transform_edt(site_mask)
    dist_m = dist_px * px_size
    access = 1.0 / (1.0 + dist_m / (decay_km * 1000))
    return access


def pd_concat_points(a: gpd.GeoDataFrame, b: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    import pandas as pd
    return gpd.GeoDataFrame(pd.concat([a[["geometry"]], b[["geometry"]]], ignore_index=True), crs=a.crs)


def classify(barrier: np.ndarray, access: np.ndarray) -> np.ndarray:
    valid = ~np.isnan(barrier) & ~np.isnan(access)
    b_med = np.nanmedian(barrier[valid])
    a_med = np.nanmedian(access[valid])
    high_barrier = barrier >= b_med
    high_access = access >= a_med
    out = np.select(
        [~valid, high_barrier & high_access, high_barrier & ~high_access, ~high_barrier & high_access],
        [np.nan, 3, 1, 2],  # 1=conservation_priority, 2=compatible_access, 3=conflict
        default=0,  # low barrier, low access
    )
    return out.astype(float)


def build_road_tradeoff() -> None:
    dist_road = rioxarray.open_rasterio(
        COVARIATE_DIR / "distance_to_road_m.tif", masked=True
    ).squeeze("band", drop=True)
    barrier = 1.0 / (1.0 + dist_road.values / 1000.0)
    access = access_value_kernel(dist_road)
    access = np.where(np.isnan(dist_road.values), np.nan, access)

    cls = classify(barrier, access)
    for name, arr in [("road_barrier_severity", barrier), ("road_access_value", access),
                       ("road_tradeoff_class", cls)]:
        out = dist_road.copy(data=np.where(np.isnan(dist_road.values), np.nan, arr))
        out.rio.to_raster(OUT_DIR / f"{name}.tif", compress="LZW")
    print("Road trade-off maps written")


def build_waterway_tradeoff() -> None:
    water_res = rioxarray.open_rasterio(
        RESISTANCE_DIR / "water_resistance.tif", masked=True
    ).squeeze("band", drop=True)
    barrier = water_res.values / 100.0  # normalize resistance (1-100) to (0-1]
    access = access_value_kernel(water_res)
    access = np.where(np.isnan(water_res.values), np.nan, access)

    cls = classify(barrier, access)
    for name, arr in [("waterway_barrier_severity", barrier), ("waterway_access_value", access),
                       ("waterway_tradeoff_class", cls)]:
        out = water_res.copy(data=np.where(np.isnan(water_res.values), np.nan, arr))
        out.rio.to_raster(OUT_DIR / f"{name}.tif", compress="LZW")
    print("Waterway trade-off maps written")


def main() -> None:
    build_road_tradeoff()
    build_waterway_tradeoff()


if __name__ == "__main__":
    main()
