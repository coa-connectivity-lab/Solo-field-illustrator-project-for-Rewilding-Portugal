"""
validate_results.py
──────────────────────
Sanity checks before the results are trusted enough to map or narrate:
  1. All Omniscape output rasters share grid/CRS/extent.
  2. Connectivity is lower under roads/high-imperviousness than in open
     corridor stretches (a basic direction-of-effect check, not a
     statistical validation - Prima et al. 2024 flag connectivity-model
     validation as a field-wide gap, p.2396, and this project has no
     movement-tracking data to validate against).
"""

import numpy as np
import rioxarray

import config

RASTER_DIR = config.OUTPUT_RASTERS
COVARIATE_DIR = config.DATA_PROCESSED / "covariates"


def check_grid_alignment() -> bool:
    names = [f"{g}_normalized_current" for g in config.GROUPS] + [
        "multispecies_mean_connectivity", "multispecies_max_connectivity"
    ]
    refs = []
    ok = True
    for name in names:
        da = rioxarray.open_rasterio(RASTER_DIR / f"{name}.tif")
        refs.append((name, da.shape, da.rio.crs, da.rio.transform()))
    base = refs[0]
    for name, shape, crs, transform in refs[1:]:
        if shape != base[1] or crs != base[2] or transform != base[3]:
            print(f"  MISMATCH: {name} vs {base[0]}")
            ok = False
    print(f"Grid alignment: {'OK' if ok else 'FAILED'} ({len(refs)} rasters checked)")
    return ok


def check_road_effect() -> None:
    """Land-group normalized current should be lower near roads than far from them."""
    land = rioxarray.open_rasterio(RASTER_DIR / "land_normalized_current.tif", masked=True).squeeze("band", drop=True)
    dist_road = rioxarray.open_rasterio(COVARIATE_DIR / "distance_to_road_m.tif", masked=True).squeeze("band", drop=True)
    dist_road_on_land_grid = dist_road.interp_like(land, method="nearest")

    valid = ~np.isnan(land.values) & ~np.isnan(dist_road_on_land_grid.values)
    d = dist_road_on_land_grid.values[valid]
    c = land.values[valid]
    near = c[d < np.percentile(d, 25)]
    far = c[d > np.percentile(d, 75)]
    print(f"Land connectivity near roads (<25th pct distance): mean {near.mean():.3f}")
    print(f"Land connectivity far from roads (>75th pct distance): mean {far.mean():.3f}")
    if near.mean() < far.mean():
        print("  Direction as expected: lower connectivity near roads.")
    else:
        print("  WARNING: connectivity is not lower near roads - check resistance/source inputs.")


def check_survey_barriers() -> None:
    """Cross-check Survey123 barrier permeability notes against modelled road resistance, where present."""
    import geopandas as gpd
    visited = gpd.read_file(config.DATA_PROCESSED / "field_observations.gpkg", layer="visited_sites")
    print(f"Survey123 visited sites available for spot-check: {len(visited)} "
          "(barrier-type/permeability fields are free text in this prototype export - "
          "see acquire_field_observations.py docstring - so this is a manual read, not automated).")


def main() -> None:
    check_grid_alignment()
    check_road_effect()
    check_survey_barriers()


if __name__ == "__main__":
    main()
