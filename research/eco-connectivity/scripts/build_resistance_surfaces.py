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
"""

import numpy as np
import rioxarray

import config

SUITABILITY_DIR = config.DATA_PROCESSED / "suitability"
FIRE_RASTER = config.DATA_PROCESSED / "covariates" / "fire_last_burn_year.tif"
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

        out = da.copy(data=resistance)
        out_path = OUT_DIR / f"{group_key}_resistance.tif"
        out.rio.to_raster(out_path, compress="LZW")
        valid = resistance[~np.isnan(resistance)]
        print(f"{group.label}: c={group.resistance_shape_c}, "
              f"resistance range [{valid.min():.1f}, {valid.max():.1f}], mean {valid.mean():.1f}")
        print(f"  wrote {out_path}")


if __name__ == "__main__":
    main()
