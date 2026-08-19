"""
acquire_environmental_covariates.py
────────────────────────────────────
Clip the environmental covariates the suitability models need to the Côa
Valley study area, reading raw material from the sibling data-management
repo (read-only) and writing clipped copies into this repo's data/processed/.

Rasters (from data-management/data/processed/base_layers/, EPSG:3035, 100m):
  elevation, slope_degrees, ruggedness_tri, hillshade,
  road_raster, motorway_raster, distance_to_road_m,
  landcover_clcplus, imperviousness

Vectors (from data-management/data/raw/, official EU/national sources):
  Natura 2000 (EEA, end-2024 release) — protected-area context
  Portugal surface water bodies (EEA/APA WISE) — hydrology context,
    the authoritative source for "waterways other than the Côa"
"""

import geopandas as gpd
import rioxarray  # noqa: F401 - registers the .rio accessor

import config

RASTER_NAMES = [
    "elevation",
    "slope_degrees",
    "ruggedness_tri",
    "hillshade",
    "road_raster",
    "motorway_raster",
    "distance_to_road_m",
    "landcover_clcplus",
    "imperviousness",
]

NATURA2000_GPKG = config.DATA_MGMT_RAW / "eea" / "natura2000" / "Natura2000_end2024.gpkg"
WATER_BODIES_GPKG = config.DATA_MGMT_RAW / "eea" / "hydro" / "portugal_water_bodies.gpkg"

OUT_RASTER_DIR = config.DATA_PROCESSED / "covariates"
OUT_VECTOR_GPKG = config.DATA_PROCESSED / "hydrology_and_protected_areas.gpkg"


def _study_area_metric():
    gdf = gpd.read_file(config.DATA_PROCESSED / "study_area.gpkg", layer="study_area")
    return gdf


def clip_rasters(study_area) -> None:
    OUT_RASTER_DIR.mkdir(parents=True, exist_ok=True)
    bounds = study_area.total_bounds  # minx, miny, maxx, maxy in EPSG:3035
    for name in RASTER_NAMES:
        src = config.DATA_MGMT_BASE_LAYERS / f"{name}.tif"
        if not src.exists():
            print(f"  MISSING: {src} — skipped")
            continue
        da = rioxarray.open_rasterio(src, masked=True)
        clipped = da.rio.clip_box(*bounds)
        clipped = clipped.rio.clip(study_area.geometry, study_area.crs, drop=False)
        out_path = OUT_RASTER_DIR / f"{name}.tif"
        clipped.rio.to_raster(out_path, compress="LZW")
        print(f"  {name}: {clipped.shape} -> {out_path}")


def clip_vectors(study_area) -> None:
    # Natura2000_end2024.gpkg is natively EPSG:3035 — the bbox filter must be
    # passed in the *source* file's CRS, not EPSG:4326, or pyogrio silently
    # returns zero features (degrees vs. metres, no overlap).
    bounds = tuple(study_area.total_bounds)  # already EPSG:3035

    print("  Reading Natura 2000 (bbox-filtered, source is large)...")
    natura = gpd.read_file(NATURA2000_GPKG, layer="NaturaSite_polygon", bbox=bounds)
    natura = natura.to_crs(config.CRS_METRIC)
    natura = gpd.clip(natura, study_area)
    natura.to_file(OUT_VECTOR_GPKG, layer="natura2000", driver="GPKG")
    print(f"  natura2000: {len(natura)} features")

    water = gpd.read_file(WATER_BODIES_GPKG)
    if water.crs is None:
        water = water.set_crs(config.CRS_DISPLAY)
    water = water.to_crs(config.CRS_METRIC)
    water = gpd.clip(water, study_area)
    water.to_file(OUT_VECTOR_GPKG, layer="water_bodies", driver="GPKG")
    print(f"  water_bodies: {len(water)} features")


def main() -> None:
    study_area = _study_area_metric()
    print("Clipping rasters...")
    clip_rasters(study_area)
    print("Clipping vectors...")
    clip_vectors(study_area)


if __name__ == "__main__":
    main()
