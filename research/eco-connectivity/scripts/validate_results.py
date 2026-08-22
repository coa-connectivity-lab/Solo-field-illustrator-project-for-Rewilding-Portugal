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
    """v3: a real automated check, replacing the print-only placeholder this used to be
    now that barrier_observations carries a structured permeability_assessment field
    (not free text) and build_resistance_surfaces.py's barrier_penalty() actually burns
    it into the resistance surfaces. Same direction-of-effect style as check_road_effect()
    above: "Fully blocking" barrier points should sit in measurably higher-resistance
    cells than "Easily crossable" ones, on whichever group(s) that barrier type maps to
    (config.BARRIER_TYPE_TO_GROUPS)."""
    import geopandas as gpd

    barriers = gpd.read_file(config.DATA_PROCESSED / "field_observations.gpkg", layer="barrier_observations")
    eligible = barriers[barriers["resistance_eligible"]]
    print(f"Survey123 barrier_observations: {len(barriers)} rows, {len(eligible)} resistance_eligible")

    for group_key in config.GROUPS:
        resistance_path = config.DATA_PROCESSED / "resistance" / f"{group_key}_resistance.tif"
        if not resistance_path.exists():
            continue
        relevant = eligible[eligible["barrier_type"].map(
            lambda bt: group_key in config.BARRIER_TYPE_TO_GROUPS.get(bt, [])
        )]
        blocking = relevant[relevant["permeability_assessment"] == "Fully blocking"]
        crossable = relevant[relevant["permeability_assessment"] == "Easily crossable"]
        if blocking.empty or crossable.empty:
            print(f"  {group_key}: not enough of both tiers to compare "
                  f"({len(blocking)} fully blocking, {len(crossable)} easily crossable) - skipping")
            continue

        resistance = rioxarray.open_rasterio(resistance_path, masked=True).squeeze("band", drop=True)
        transform = resistance.rio.transform()
        rows, cols = resistance.shape

        def _sample(points) -> np.ndarray:
            vals = []
            for geom in points.geometry:
                col, row = ~transform * (geom.x, geom.y)
                row, col = int(row), int(col)
                if 0 <= row < rows and 0 <= col < cols:
                    v = resistance.values[row, col]
                    if not np.isnan(v):
                        vals.append(v)
            return np.array(vals)

        blocking_vals = _sample(blocking)
        crossable_vals = _sample(crossable)
        if len(blocking_vals) == 0 or len(crossable_vals) == 0:
            print(f"  {group_key}: barrier points fell outside the resistance grid - skipping")
            continue

        print(f"  {group_key}: 'Fully blocking' resistance mean {blocking_vals.mean():.1f} "
              f"(n={len(blocking_vals)}); 'Easily crossable' resistance mean {crossable_vals.mean():.1f} "
              f"(n={len(crossable_vals)})")
        if blocking_vals.mean() > crossable_vals.mean():
            print("    Direction as expected: 'Fully blocking' sits in higher-resistance cells.")
        else:
            print("    WARNING: 'Fully blocking' is not higher-resistance than 'Easily crossable' - "
                  "check barrier_penalty().")


def main() -> None:
    check_grid_alignment()
    check_road_effect()
    check_survey_barriers()


if __name__ == "__main__":
    main()
