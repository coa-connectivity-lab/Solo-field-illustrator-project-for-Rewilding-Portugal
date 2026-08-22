"""
build_resistance_surfaces.py
──────────────────────────────
Convert each group's suitability raster to a resistance raster via
Prima et al. 2024's Eq.1 (p.2389):

    R = 100 - 99 * (1 - exp(-c*H)) / (1 - exp(-c))

H = suitability in [0,1], R in [1,100] (1 = no resistance, 100 = impassable).
Single mid-range c per group (config.Group.resistance_shape_c), not Prima's
c-sweep - this project's "single best-estimate" scoping decision.

v2 addition — fire as a barrier to land restoration: after the Eq.1 transform, the
**land** group gets an additional recency-scaled penalty added on top, from
data/processed/covariates/fire_last_burn_year.tif (built by acquire_fire_history.py,
real MODIS MCD64A1 burned-area history, not a proxy). A cell that burned more recently
within config.FIRE_HISTORY_START–FIRE_HISTORY_END is pushed further toward the
resistance ceiling than one that burned longer ago; never-burned cells are unaffected.
Land-group-only, per the ask — water/air groups are untouched (post-fire
erosion/sediment effects on the water group are a documented open item, not modeled
here, to keep this addition contained).

v3 addition — two more penalty mechanisms, conceptually different from each other and
from the fire penalty above, both applied *after* the fire penalty in main():

  barrier_penalty() — POINT-distance-decay. Survey123's barrier_observations layer
  (acquire_field_observations.py) logs discrete barrier locations (fences, roads, dams,
  ...) with a permeability call ("Fully blocking"/"Partially crossable"/"Easily
  crossable"). Each `resistance_eligible` barrier decays a permeability-tiered penalty
  outward from its point location using the *same* distance_transform_edt-on-the-
  raster's-own-grid mechanic as build_tradeoff_maps.py's access_value_kernel (reused
  deliberately, not reinvented) — but with a tight, local decay length
  (config.BARRIER_PENALTY_DECAY_M = 500m, vs. access_value_kernel's 5km) since this is
  a point field observation, not a landscape-scale covariate. Barriers are grouped by
  permeability tier (one distance transform per tier that's present, not one per point -
  within a tier, penalty is a monotonic function of distance, so the nearest point of
  that tier already gives that tier's max contribution at every cell); the per-tier
  penalty rasters then combine via np.maximum - worst-nearby-barrier wins, same
  "recency wins" logic the fire penalty already uses. Only applied to the group(s) each
  barrier_type maps to via config.BARRIER_TYPE_TO_GROUPS - terrestrial barrier types
  affect Land only, Dam/Weir/Culvert affect Water only (this fills the gap
  build_tradeoff_maps.py's own docstring names about no dedicated dam/weir point layer
  existing for the waterway trade-off's barrier_severity term), Bridge affects both.

  heritage_conflict_penalty() — AREA-fill, NOT distance-decayed. The two UNESCO World
  Heritage polygons in data/processed/heritage_protection.gpkg (acquire_unesco_heritage_
  zones.py) represent whole protected landscapes that are uniformly poor/unavailable
  matrix across their *entire* extent, not something that fades out from an edge the way
  a fence or a fire scar does - so this rasterizes the polygon(s) directly onto the
  group's grid (rasterio.features.rasterize; rioxarray's own .rio.clip() clips *to* a
  polygon rather than burning a flag *onto* the full grid, so it doesn't fit this
  area-fill use case - this is genuinely new machinery for this codebase, no existing
  script does a polygon-area burn) and applies a fixed near-ceiling penalty
  (config.HERITAGE_CONFLICT_PENALTY) across every cell inside. Applied only to
  config.HERITAGE_CONFLICT_GROUPS (Land).

Both new penalties cap the running total at the same ceiling the fire penalty already
respects (config.FIRE_RESISTANCE_CEILING). Neither is applied to the Air group - stated
here as an explicit open item, not silently omitted: raptors are not meaningfully
barred by a fence or a vineyard terrace the way a fox or an otter is, but a heritage
zone's disturbance regime (tourism, low-altitude aircraft/drone restrictions near rock
art panels) could plausibly matter to Air connectivity too - this pass doesn't model
that, it's left for a future iteration.

Also unresolved, by design, not by omission: the new Road/Motorway barrier_observations
points overlap conceptually with the existing continuous distance_to_road_m suitability
covariate that already feeds every group's Eq.1 resistance. This is documented here
rather than algorithmically reconciled - the covariate is a continuous proximity effect
baked into suitability, while the new barrier points are discrete, permeability-scored
field observations at specific crossings; collapsing them into one signal would need a
judgment call about double-counting that's out of scope for this pass.
"""

import geopandas as gpd
import numpy as np
import pandas as pd
import rioxarray
from rasterio.features import rasterize
from scipy.ndimage import distance_transform_edt

import config

SUITABILITY_DIR = config.DATA_PROCESSED / "suitability"
FIRE_RASTER = config.DATA_PROCESSED / "covariates" / "fire_last_burn_year.tif"
BARRIER_GPKG = config.DATA_PROCESSED / "field_observations.gpkg"
HERITAGE_GPKG = config.DATA_PROCESSED / "heritage_protection.gpkg"
HERITAGE_LAYERS = ["unesco_alto_douro", "coa_rock_art_core"]
OUT_DIR = config.DATA_PROCESSED / "resistance"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def suitability_to_resistance(h: np.ndarray, c: float) -> np.ndarray:
    return 100 - 99 * (1 - np.exp(-c * h)) / (1 - np.exp(-c))


def fire_penalty(last_burn_year: np.ndarray) -> np.ndarray:
    """0 for never-burned cells; scales from FIRE_RESISTANCE_MIN_PENALTY (burned at the
    start of the window) up to FIRE_RESISTANCE_MAX_PENALTY (burned in the most recent
    year present) for burned cells."""
    start_year = int(config.FIRE_HISTORY_START[:4])
    end_year = int(config.FIRE_HISTORY_END[:4])
    span = max(end_year - start_year, 1)
    recency_frac = np.clip((last_burn_year - start_year) / span, 0.0, 1.0)
    penalty_range = config.FIRE_RESISTANCE_MAX_PENALTY - config.FIRE_RESISTANCE_MIN_PENALTY
    return np.where(
        last_burn_year > 0,
        config.FIRE_RESISTANCE_MIN_PENALTY + penalty_range * recency_frac,
        0.0,
    )


def apply_fire_penalty_to_land(resistance: np.ndarray) -> np.ndarray:
    if not FIRE_RASTER.exists():
        print(f"  WARNING: {FIRE_RASTER} not found - skipping fire penalty, land resistance is fire-unaware "
              f"(run acquire_fire_history.py first)")
        return resistance

    fire_da = rioxarray.open_rasterio(FIRE_RASTER, masked=False).squeeze("band", drop=True)
    if fire_da.shape != resistance.shape:
        raise ValueError(
            f"fire_last_burn_year.tif shape {fire_da.shape} != land resistance shape {resistance.shape} - "
            "these must share the same grid (both should derive from the same extended study area covariates)."
        )

    penalty = fire_penalty(fire_da.values)
    n_penalized = (penalty > 0).sum()
    print(f"  Fire penalty applied to {n_penalized} cells ({n_penalized / penalty.size * 100:.2f}% of grid), "
          f"penalty range [{config.FIRE_RESISTANCE_MIN_PENALTY:.0f}, {config.FIRE_RESISTANCE_MAX_PENALTY:.0f}]")
    return np.minimum(resistance + penalty, config.FIRE_RESISTANCE_CEILING)


def barrier_penalty(group_key: str, template) -> np.ndarray:
    """Point-distance-decay penalty from barrier_observations (see module docstring).
    Returns a same-shape-as-template array, 0 where no eligible barrier for this group
    is nearby."""
    rows, cols = template.shape
    penalty = np.zeros((rows, cols))

    if not BARRIER_GPKG.exists():
        print(f"  WARNING: {BARRIER_GPKG} not found - skipping barrier penalty for {group_key} "
              f"(run acquire_field_observations.py first)")
        return penalty

    barriers = gpd.read_file(BARRIER_GPKG, layer="barrier_observations").to_crs(template.rio.crs)
    eligible = barriers[barriers["resistance_eligible"]]
    relevant = eligible[eligible["barrier_type"].map(
        lambda bt: group_key in config.BARRIER_TYPE_TO_GROUPS.get(bt, [])
    )]
    if relevant.empty:
        return penalty

    transform = template.rio.transform()
    px_size = abs(transform.a)

    for tier, weight in config.BARRIER_PERMEABILITY_PENALTY.items():
        tier_rows = relevant[relevant["permeability_assessment"] == tier]
        if tier_rows.empty:
            continue
        point_mask = np.ones((rows, cols), dtype=bool)
        n_in_grid = 0
        for geom in tier_rows.geometry:
            col, row = ~transform * (geom.x, geom.y)
            row, col = int(row), int(col)
            if 0 <= row < rows and 0 <= col < cols:
                point_mask[row, col] = False
                n_in_grid += 1
        if n_in_grid == 0:
            continue
        dist_m = distance_transform_edt(point_mask) * px_size
        tier_penalty = weight / (1.0 + dist_m / config.BARRIER_PENALTY_DECAY_M)
        penalty = np.maximum(penalty, tier_penalty)

    return penalty


def apply_barrier_penalty(group_key: str, resistance: np.ndarray, template) -> np.ndarray:
    penalty = barrier_penalty(group_key, template)
    nonzero = penalty[penalty > 0]
    # 1/(1+dist/decay) is the same long-tailed kernel shape as access_value_kernel - it
    # never truly reaches 0 at finite distance, so "cells touched at all" is a much
    # bigger number than "cells meaningfully affected". Report both.
    n_touched = int((penalty > 0).sum())
    n_meaningful = int((penalty >= 1.0).sum())
    if n_touched:
        print(f"  Barrier penalty: {n_meaningful} cells with >=1.0 resistance added "
              f"({n_touched} touched at all), range [{nonzero.min():.2f}, {nonzero.max():.1f}], "
              f"decay {config.BARRIER_PENALTY_DECAY_M:.0f}m, peak weights {config.BARRIER_PERMEABILITY_PENALTY}")
    return np.minimum(resistance + penalty, config.FIRE_RESISTANCE_CEILING)


def heritage_conflict_penalty(group_key: str, template) -> np.ndarray:
    """Area-fill penalty from the two UNESCO heritage_protection.gpkg polygons - NOT
    distance-decayed (see module docstring for why this is a different mechanism from
    barrier_penalty above). Only non-zero for config.HERITAGE_CONFLICT_GROUPS."""
    rows, cols = template.shape
    if group_key not in config.HERITAGE_CONFLICT_GROUPS:
        return np.zeros((rows, cols))

    if not HERITAGE_GPKG.exists():
        print(f"  WARNING: {HERITAGE_GPKG} not found - skipping heritage-conflict penalty for "
              f"{group_key} (run acquire_unesco_heritage_zones.py first)")
        return np.zeros((rows, cols))

    gdfs = [gpd.read_file(HERITAGE_GPKG, layer=layer) for layer in HERITAGE_LAYERS]
    polys = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs).to_crs(template.rio.crs)

    burned = rasterize(
        [(geom, 1) for geom in polys.geometry],
        out_shape=(rows, cols),
        transform=template.rio.transform(),
        fill=0,
        dtype="uint8",
    )
    return np.where(burned == 1, config.HERITAGE_CONFLICT_PENALTY, 0.0)


def apply_heritage_penalty(group_key: str, resistance: np.ndarray, template) -> np.ndarray:
    penalty = heritage_conflict_penalty(group_key, template)
    n_penalized = int((penalty > 0).sum())
    if n_penalized:
        print(f"  Heritage-conflict penalty applied to {n_penalized} cells "
              f"({n_penalized / penalty.size * 100:.2f}% of grid), flat penalty {config.HERITAGE_CONFLICT_PENALTY:.0f}")
    return np.minimum(resistance + penalty, config.FIRE_RESISTANCE_CEILING)


def main() -> None:
    for group_key, group in config.GROUPS.items():
        da = rioxarray.open_rasterio(
            SUITABILITY_DIR / f"{group_key}_suitability.tif", masked=True
        ).squeeze("band", drop=True)
        resistance = suitability_to_resistance(da.values, group.resistance_shape_c)

        if group_key == "land":
            # Kept as a diagnostic byproduct so the fire-penalty effect can be shown
            # as a before/after comparison map (generate_maps.map_10_fire_effect).
            no_fire_out = da.copy(data=resistance)
            no_fire_out.rio.to_raster(OUT_DIR / "land_resistance_no_fire.tif", compress="LZW")
            resistance = apply_fire_penalty_to_land(resistance)

        if group_key in ("land", "water"):
            # Air is deliberately excluded - see module docstring's open item.
            resistance = apply_barrier_penalty(group_key, resistance, da)

        if group_key in config.HERITAGE_CONFLICT_GROUPS:
            resistance = apply_heritage_penalty(group_key, resistance, da)

        out = da.copy(data=resistance)
        out_path = OUT_DIR / f"{group_key}_resistance.tif"
        out.rio.to_raster(out_path, compress="LZW")
        valid = resistance[~np.isnan(resistance)]
        print(f"{group.label}: c={group.resistance_shape_c}, "
              f"resistance range [{valid.min():.1f}, {valid.max():.1f}], mean {valid.mean():.1f}")
        print(f"  wrote {out_path}")


if __name__ == "__main__":
    main()
